"""
GenePattern Module Creator

Tools for converting Python scripts into GenePattern server modules

Compatible with Python 2.7 and Python 3.4+
"""

import json
import os
import string
import zipfile
from enum import Enum
from datetime import datetime

__authors__ = ['Thorin Tabor']
__version__ = '0.1.0'
__status__ = 'Beta'


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


class GPTaskSpec:
    """
    Specification needed to create a new GenePattern module
    """

    def __init__(self, name=None, description="", version_comment="", author="", institution="",
                 categories=[], privacy=Privacy.PRIVATE, quality=Quality.DEVELOPMENT,
                 file_format=[], os=OS.ANY, cpu=CPU.ANY, language="Python",
                 user=None, support_files=[], documentation="", license="",
                 lsid=None, command_line=None, parameters=[]):

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

        self.lsid = lsid
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

    def create_zip(self, clean=True):
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

        # Clean up the manifest
        if clean:
            os.remove(MANIFEST_FILE_NAME)

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
        manifest_file.write("LSID=" + self.manifest_escape(self.lsid) + "\n")
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

        if self.lsid.count(':') != 5:
            raise ValueError("lsid contains incorrect number of colons, 5 expected: " + str(self.lsid))

        if self.lsid.split(':')[0].lower() != 'urn':
            raise ValueError("lsid does not begin with urn: " + str(self.lsid))

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
