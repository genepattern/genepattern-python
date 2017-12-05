"""
GenePattern Module Creator

Tools for converting Python scripts into GenePattern server modules

Compatible with Python 3.4+
"""
import getpass
import json
import os
import pathlib
import socket
import string
import zipfile
from enum import Enum
from datetime import datetime

import re

from gp import GPServer

__authors__ = ['Thorin Tabor']
__version__ = '0.2.0'
__status__ = 'Alpha'


class StringEnum(str, Enum):
    """
    Enum where members are also (and must be) strings
    Necessary for JSON serialization of the Enums declared here
    """


class Privacy(StringEnum):
    PRIVATE = "private"
    PUBLIC = "public"


class Quality(StringEnum):
    DEVELOPMENT = "development"
    PREPRODUCTION = "preproduction"
    PRODUCTION = "production"


class OS(StringEnum):
    ANY = "any"
    LINUX = "linux"
    MAC = "mac"
    WINDOWS = "windows"


class CPU(StringEnum):
    ANY = "any"
    ALPHA = "alpha"
    INTEL = "intel"
    POWERPC = "powerpc"
    SPARC = "sparn"


MANIFEST_FILE_NAME = "manifest"
DEFAULT_LSID_AUTHORITY = 0


class GPTaskSpec:
    """
    Specification needed to create a new GenePattern module
    """

    def __init__(self, name=None, description="", version_comment="", author="", institution="",
                 categories=[], privacy=Privacy.PRIVATE, quality=Quality.DEVELOPMENT,
                 file_format=[], os=OS.ANY, cpu=CPU.ANY, language="Python",
                 user=None, support_files=[], documentation="", license="",
                 lsid=None, version=1, lsid_authority=DEFAULT_LSID_AUTHORITY, command_line=None, parameters=[]):

        self.name = name
        self.description = description
        self.version_comment = version_comment
        self.author = author
        self.institution = institution

        self.categories = categories
        self.privacy = privacy
        self.quality = quality

        self.file_format = file_format
        self.os = os
        self.cpu = cpu
        self.language = language

        self.user = user
        self.support_files = support_files
        self.documentation = documentation
        self.license = license

        # Use None for no LSID checking
        self.lsid_authority = lsid_authority if lsid_authority != DEFAULT_LSID_AUTHORITY else LSIDAuthority()
        self.version = version
        self.lsid = lsid if lsid else self._get_lsid()
        self.command_line = command_line
        self.parameters = parameters

    def validate(self):
        """
        Perform some basic checks to help ensure that the specification is valid.
        Throws an exception if an invalid value is found.
        Returns true if all checks were passed.
        :return: boolean
        """
        # Check all values for None
        for attr in self.__dict__:
            if self.__dict__[attr] is None:
                raise ValueError(attr + " is not set")

        # Validate name
        invalid_chars = GPTaskSpec.invalid_chars()
        if any(char in invalid_chars for char in self.name):
            raise ValueError("module name includes invalid characters: " + self.name)

        # Validate LSID
        self._valid_lsid()

        # Validate categories
        if not self.all_strings(self.categories):
            raise TypeError("categories contains non-string value: " + str(self.categories))

        # Validate file formats
        if not self.all_strings(self.file_format):
            raise TypeError("file_format contains non-string value: " + str(self.file_format))

        # Validate support files
        if not self.all_strings(self.support_files):
            raise TypeError("support_files contains non-string value: " + str(self.support_files))

        # Validate parameter list
        if not self._all_params(self.parameters):
            raise TypeError("parameters contains non-GPParamSpec value: " + str(self.parameters))

        # Validate individual parameters
        for param in self.parameters:
            param.validate()

        # Return that everything validates
        return True

    def create_zip(self, clean=True, increment_version=True, register=True):
        """
        Creates a GenePattern module zip file for upload and installation on a GenePattern server
        :param clean: boolean
        :return:
        """
        # First validate the attributes
        self.validate()

        # Check to see if an existing interferes with module creation
        if os.path.exists(MANIFEST_FILE_NAME):
            raise OSError("existing manifest blocks manifest file creation")

        # Write the manifest
        self.write_manifest()

        # Create the zip
        self._zip_files()

        # Increment the version of the module
        if increment_version:
            self.version += 1

        # Register the module with the LSID authority
        if register and self.lsid_authority:
            self.lsid_authority.register(self)

        # Clean up the manifest
        if clean:
            os.remove(MANIFEST_FILE_NAME)

    def _get_lsid(self):
        """
        Assigns the module an LSID from the LSID authority
        :return:
        """
        # If no LSID authority, skip LSID assignment
        if self.lsid_authority is None:
            return

        # Otherwise assign the LSID
        return self.lsid_authority.lsid()

    def _zip_files(self):
        """
        Adds the manifest and all support files to the zip file
        :return:
        """
        # Create the zip file
        zip = zipfile.ZipFile(self.name + '.zip', 'w', zipfile.ZIP_DEFLATED)

        # Add the manifest file to the zip
        zip.write(MANIFEST_FILE_NAME)

        # Add the support files to the zip
        for file in self.support_files:
            zip.write(file)

        # Close the zip file
        zip.close()

    def write_manifest(self, module_directory=""):
        """
        Write a GenePattern manifest file for the module
        :param module_directory: optionally write to subdirectory
        :return:
        """
        # First validate the spec
        self.validate()

        # Open the manifest file for writing
        manifest_file = open(os.path.join(module_directory, "manifest"), "w")

        # Write the header
        manifest_file.write("# " + self.name + "\n")
        manifest_file.write("# " + str(datetime.now()) + "\n")
        manifest_file.write("# Generated by Python Module Creator v" + __version__ + "\n")

        # Write initial attributes
        manifest_file.write("JVMLevel=\n")
        manifest_file.write("LSID=" + self.manifest_escape(self.lsid) + ':' + str(self.version) + "\n")
        manifest_file.write("author=" + self._author_line() + "\n")
        manifest_file.write("categories=" + ';'.join(self.categories) + "\n")
        manifest_file.write("commandLine=" + self.command_line + "\n")
        manifest_file.write("cpuType=" + str(self.cpu.value) + "\n")
        manifest_file.write("description=" + self.description + "\n")
        manifest_file.write("fileFormat=" + ';'.join(self.file_format) + "\n")
        manifest_file.write("language=" + self.language + "\n")
        manifest_file.write("license=" + self.license + "\n")
        manifest_file.write("name=" + self.name + "\n")
        manifest_file.write("os=" + str(self.os.value) + "\n")

        # Write parameter attributes
        for index, param in enumerate(self.parameters):
            manifest_file.write(param.manifest_repr(index+1))

        # Write footer attributes
        manifest_file.write("privacy=" + str(self.privacy.value) + "\n")
        manifest_file.write("publicationDate=" + self._publication_date() + "\n")
        manifest_file.write("quality=" + str(self.quality.value) + "\n")
        manifest_file.write("taskDoc=" + self.documentation + "\n")
        manifest_file.write("taskType=" + self._task_type() + "\n")
        manifest_file.write("userid=" + self.user + "\n")
        manifest_file.write("version=" + self.version_comment + "\n")

        # Close the file
        manifest_file.close()

    def _author_line(self):
        """
        Helper method to concatenate author and institution values, if necessary
        :return: string
        """
        if self.author and self.institution:
            return self.author + ";" + self.institution
        elif self.author:
            return self.author
        else:
            return self.institution

    @staticmethod
    def _publication_date():
        """
        Helper method to return the publication date in the expected format
        :return: string
        """
        return datetime.now().strftime("%m/%d/%Y %H\:%M")

    def _task_type(self):
        """
        Helper method for extracting taskType from the categories list
        :return:
        """
        if self.categories:
            return self.categories[0]
        else:
            return ""

    @staticmethod
    def manifest_escape(string):
        """
        Escape colon and equals characters for inclusion in manifest file
        :param string:
        :return: string
        """
        return string.replace(':', '\:').replace('=', '\=')

    @staticmethod
    def all_strings(arr):
        """
        Ensures that the argument is a list that either is empty or contains only strings
        :param arr: list
        :return:
        """
        if not isinstance([], list):
            raise TypeError("non-list value found where list is expected")
        return all(isinstance(x, str) for x in arr)

    @staticmethod
    def _all_params(arr):
        """
        Ensures that the argument is a list that either is empty or contains only GPParamSpec's
        :param arr: list
        :return:
        """
        if not isinstance([], list):
            raise TypeError("non-list value found for parameters")
        return all(isinstance(x, GPParamSpec) for x in arr)

    def _valid_lsid(self):
        """
        Performs some basic (non-comprehensive) LSID validation
        :return:
        """
        if not isinstance(self.lsid, str):
            raise TypeError("lsid is not a string, string expected: " + str(self.lsid))

        if self.lsid.count(':') != 4:
            raise ValueError("lsid contains incorrect number of colons, 4 expected: " + str(self.lsid))

        if self.lsid.split(':')[0].lower() != 'urn':
            raise ValueError("lsid does not begin with urn: " + str(self.lsid))

        # If an LSID authority is specified, check with the authority
        if self.lsid_authority:
            if not self.lsid_authority.validate(self.lsid, check_existing=False):
                raise ValueError("lsid does not the authority: " + str(self.lsid))

    @staticmethod
    def invalid_chars():
        """
        Returns a set of characters which are not valid in module or parameter names
        :return:
        """
        return set(string.punctuation.replace("_", "").replace(".", "") + string.whitespace)


class Type(StringEnum):
    FILE = "FILE"
    TEXT = "TEXT"
    INTEGER = "Integer"
    FLOATING_POINT = "Floating Point"
    DIRECTORY = "DIRECTORY"
    PASSWORD = "PASSWORD"


class JavaType(StringEnum):
    FILE = "java.io.File"
    TEXT = "java.lang.String"
    INTEGER = "java.lang.Integer"
    FLOATING_POINT = "java.lang.Float"
    DIRECTORY = "DIRECTORY"
    PASSWORD = "PASSWORD"


class Optional(StringEnum):
    REQUIRED = ""
    OPTIONAL = "on"


class GPParamSpec:
    """
    Specification needed to create a parameter for a new GenePattern module
    """
    def __init__(self, name=None, description="", optional=Optional.REQUIRED,
                 type=Type.TEXT, choices={}, value="", default_value="",
                 file_format=[], min_values=0, max_values=1,
                 flag="", prefix_when_specified=False):

        self.name = name
        self.description = description
        self.optional = optional

        self.type = type
        self.choices = choices
        self.value = value
        self.default_value = default_value

        self.file_format = file_format
        self.min_values = min_values
        self.max_values = max_values

        self.flag = flag
        self.prefix_when_specified = prefix_when_specified

    def validate(self):
        # Check all values for None, only max_values is allowed to be None
        for attr in self.__dict__:
            if self.__dict__[attr] is None and attr != "max_values":
                raise ValueError(attr + " is not set")

        # Validate name
        invalid_chars = GPTaskSpec.invalid_chars()
        if any(char in invalid_chars for char in self.name):
            raise ValueError("parameter name includes invalid characters: " + self.name)

        # Validate min_values
        if not isinstance(self.min_values, int):
            raise ValueError("min_values not an int in: " + self.name)

        # Validate max_values
        if not isinstance(self.max_values, int) and self.max_values is not None and self.max_values != float("inf"):
            raise ValueError("max_values not an int, None or infinity in: " + self.name)

        # Validate file formats
        if not GPTaskSpec.all_strings(self.file_format):
            raise TypeError("file_format contains non-string value in parameter: " + self.name)

        # Validate choices dict
        if not isinstance(self.choices, dict):
            raise TypeError("choices is not dict in parameter: " + self.name)

        # Return that everything validates
        return True

    def manifest_repr(self, p_num):
        """
        Builds a manifest string representation of the parameters and returns it
        :param p_num: int
        :return: string
        """
        # Build the parameter prefix
        prefix = "p" + str(p_num) + "_"

        # Generate the manifest string
        manifest = prefix + "MODE=" + ("IN" if self.type == Type.FILE else "") + "\n"
        manifest += prefix + "TYPE=" + str(self.type.value) + "\n"
        if self.type == Type.FILE and len(self.choices) > 0:
            manifest += prefix + "choices=" + self._choices() + "\n"
        manifest += prefix + "default_value=" + self.default_value + "\n"
        manifest += prefix + "description=" + GPTaskSpec.manifest_escape(self.description) + "\n"
        manifest += prefix + "fileFormat=" + ';'.join(self.file_format) + "\n"
        manifest += prefix + "flag=" + self.flag + "\n"
        manifest += prefix + "name=" + self.name + "\n"
        manifest += prefix + "numValues=" + self._num_values() + "\n"
        manifest += prefix + "optional=" + str(self.optional.value) + "\n"
        manifest += prefix + "prefix=" + (self.flag if self.prefix_when_specified else "") + "\n"
        manifest += prefix + "prefix_when_specified=" + (self.flag if self.prefix_when_specified else "") + "\n"
        manifest += prefix + "type=" + self._java_type() + "\n"
        manifest += prefix + "value=" + (self._choices() if self.type != Type.FILE and len(self.choices) > 0 else "") + "\n"

        # Return the manifest string
        return manifest

    def _choices(self):
        """
        Generate a string of choices as key/value pairs
        :return: string
        """
        # Generate key/value strings
        pairs = []
        for key, value in self.choices.items():
            pairs.append(str(value) + "=" + str(key))

        # Assemble into overall string and escape
        return GPTaskSpec.manifest_escape(";".join(pairs))

    def _num_values(self):
        """
        Generate a valid num_values string based off min_values and max_values
        :return: string
        """
        # Add min_values to string
        num_values = str(self.min_values) if self.min_values else "0"

        # Handle infinite max_values or finite max_values
        if self.max_values is None or self.max_values == float("inf"):
            num_values += "+"
        else:
            num_values += ".." + str(self.max_values)

        # Return the num_values string
        return num_values

    def _java_type(self):
        """
        Translates GenePattern type string to Java type string
        :return: string
        """
        return JavaType[self.type.name].value


class LSIDAuthority:
    """
    Class representing a Life Science Identifier (LSID) authority used to assign an LSID to the
    GenePattern modules produced by this package.
    """
    authority = None
    base_lsid = None
    module_count = None
    registered_modules = None

    def __init__(self, authority=None):
        """
        Initializes an LSID authority. Looks for an LSID authority file. If no such file is found,
        a file will be created with an LSID based off the machine's hostname or IP address.

        LSID authority standard location:
            ~/.genepattern/lsid_authority.json

        :param authority: Must be a file path to the LSID authority file, or a gpserver object (not implemented).
        """

        # Handle default authority file locations
        if authority is None:
            # Check for LSID authority file in user directory
            user_dir = str(pathlib.Path.home())
            gp_dir = os.path.join(user_dir, '.genepattern')
            default_authority_file = os.path.join(gp_dir, 'lsid_authority.json')
            if os.path.isfile(default_authority_file):
                # Authority file found, assign path
                authority = default_authority_file
            else:
                # No authority file found, lazily create file
                self._create_authority_file(default_authority_file)
                authority = default_authority_file

        # Handle a GenePattern server as the LSID authority
        if type(authority) == GPServer:
            raise NotImplementedError("Support for GenePattern server as a remote LSID authority is not implemented.")

        # Handle a string file path as an LSID authority
        if type(authority) == str:
            if os.path.isfile(authority):
                if os.access(authority, os.R_OK) and os.access(authority, os.W_OK):
                    try:
                        # Load the authority file
                        self.authority = authority
                        self._load_lsid_authority()
                    except Exception as e:
                        raise RuntimeError("Unable to read authority file due to: " + str(e))
                else:
                    raise RuntimeError("Missing permissions on provided LSID authority file")
            else:
                raise RuntimeError("Provided LSID authority isn't a file")

    @staticmethod
    def _generate_namespace():
        """
        Generate an LSID namespace based off Jupyter user or system user
        :return: string
        """
        raw_namespace = None

        # Get the Jupyter user, if available
        try:
            raw_namespace = os.environ['JPY_USER']
        except KeyError:
            pass

        # Otherwise get the current user
        if raw_namespace is None or raw_namespace == '':
            raw_namespace = getpass.getuser()

        # Remove illegal characters and return
        return re.sub(r'[^\w.-]', '-', raw_namespace)

    @staticmethod
    def _generate_domain():
        """
        Generate an LSID domain based off a setting file or the hostname
        :return: string
        """

        # Check for LSID domain setting file
        try:
            user_dir = str(pathlib.Path.home())
            jupyter_dir = os.path.join(user_dir, '.jupyter')
            domain_path = os.path.join(jupyter_dir, 'lsid_domain')
            with open(domain_path, 'r') as domain_file:
                domain = str(domain_file.read()).strip()
            if domain is not None and domain != '':
                return domain
        except:
            # Ignore exceptions, simply fall back to the domain name
            pass

        # If this fails, return the fully qualified domain name
        return socket.getfqdn()

    def _generate_base_lsid(self):
        """
        Generates and returns a base LSID
        :return:
        """
        domain = self._generate_domain()
        namespace = self._generate_namespace()

        # Return the base LSID
        return "urn:lsid:" + domain + ":" + namespace

    def _create_blank_authority(self):
        """
        Returns a dictionary structure representing a blank LSID authority file
        :return: dict
        """
        return {
            'base_lsid': self._generate_base_lsid(),
            'module_count': 0,
            'registered_modules': {},
        }

    def _create_authority_file(self, file_path):
        """
        Create a new LSID authority file at the indicated location
        :param file_path: location of LSID authority file
        """
        parent_dir = os.path.dirname(os.path.realpath(file_path))

        # Create the parent directory if it does not exist
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        # Create blank LSID authority structure
        blank = self._create_blank_authority()

        # Write blank structure to new authority file
        with open(file_path, 'w+') as authority_file:
            json.dump(blank, authority_file, sort_keys=True, indent=4, separators=(',', ': '))

    def _load_lsid_authority(self):
        """
        Load (or reload) the LSID authority file and set class attributes
        """
        authority_file = open(self.authority, 'r')
        authority_json = json.load(authority_file)
        authority_file.close()
        self.base_lsid = authority_json['base_lsid']
        self.module_count = int(authority_json['module_count'])
        self.registered_modules = authority_json['registered_modules']

    def _next_lsid_number(self):
        """
        Return a string representing the next module number for this LSID authority
        :return:
        """
        if self.module_count is None:
            raise Exception("Module count in LSID authority not initialized")

        return str(self.module_count+1).zfill(4)

    def _assemble_lsid(self, module_number):
        """
        Return an assembled LSID based off the provided module number and the authority's base LSID.
        Note: Never includes the module's version number.
        :param module_number:
        :return: string
        """
        if self.base_lsid is None:
            raise Exception("Base LSID in LSID authority not initialized")

        return self.base_lsid + ":" + str(module_number)

    def lsid(self):
        """
        Acquire a new LSID assigned by the LSID authority
        :return: string - assigned LSID
        """
        return self._assemble_lsid(self._next_lsid_number())

    def register(self, task_spec):
        """
        Registers a module specification with the LSID authority.
        Validates that it possesses an LSID assigned by the authority.
        Raises an exception if registration wasn't successful.
        :param task_spec:
        :return: boolean - True if registration was successful
        """
        if self.validate(task_spec.lsid):
            # Add the module name to the map
            self.registered_modules[task_spec.lsid] = task_spec.name

            # Increment module count
            self.module_count += 1

            # Write the updated LSID authority file and reload
            with open(self.authority, 'w') as authority_file:
                json.dump({
                    'base_lsid': self.base_lsid,
                    'module_count': self.module_count,
                    'registered_modules': self.registered_modules,
                }, authority_file, sort_keys=True, indent=4, separators=(',', ': '))
            self._load_lsid_authority()
        else:
            raise RuntimeError("Module LSID id not valid: " + str(task_spec.lsid))

        return True

    def validate(self, lsid, check_existing=True):
        """
        Validates an LSID with the LSID authority.
        :param lsid:
        :return: boolean - is the LSID valid with this authority?
        """
        # Base LSID matches
        if not lsid.startswith(self.base_lsid):
            return False

        # Module number isn't already taken
        if check_existing and lsid in self.registered_modules:
            return False

        # Everything checks out, return True
        return True

    def lookup(self, lsid):
        """
        Look up the name of a module by LSID assigned by the authority.
        Returns None if the LSID is not found.
        :param lsid:
        :return: string or none
        """
        if self.registered_modules is None or lsid not in self.registered_modules:
            return None
        else:
            return self.registered_modules[lsid]
