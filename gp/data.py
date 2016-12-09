__authors__ = ['Thorin Tabor']
__copyright__ = 'Copyright 2016, Broad Institute'
__version__ = '0.1.0'
__status__ = 'Beta'

"""
GenePattern Data Tools

Tools for loading GenePattern data files (such as GCT or ODF files) and
working with their contents in a Pandas DataFrame.

Compatible with Python 2.7 and Python 3.4+
"""

import re
import sys
import io

# Imports requiring compatibility between Python 2 and Python 3
if sys.version_info.major == 2:
    import urllib2
else:
    import urllib.request as urllib2


class GCT(object):
    """
    Wraps and represents a GCT file, importing the associated data
    into a pandas dataframe.

    For more information on the GCT format see:
    http://software.broadinstitute.org/cancer/software/genepattern/file-formats-guide

    :gct_obj: The GCT file. Accepts a file-like object, a file path, a URL to the file
              or a string containing the raw data.
    """
    dataframe = None

    def __init__(self, gct_obj):
        """
        Create a wrapper object for the GCT file
        """
        gct_io = None

        # Ensure that the user has pandas installed
        try:
            import pandas
        except ImportError:
            raise ImportError('pandas is required to work with a GCT file in a DataFrame.' +
                              ' Try: pip install pandas')

        # Check to see if gct_io if a GPFile object from the GenePattern Python Client, if installed
        try:
            import gp
            if isinstance(gct_obj, gp.GPFile):
                gct_io = gct_obj.open()
        except ImportError:
            pass

        # Check to see if gct_obj is a file-like object
        # Skip if a file-like object has already been obtained
        if hasattr(gct_obj, 'read') and gct_io is None:
            gct_io = gct_obj

        # Check to see if gct_obj is a string
        # Skip if a file-like object has already been obtained
        if isinstance(gct_obj, str) and gct_io is None:

            # Check to see if the string contains multiple lines
            # If it does, it is likely raw data
            if '\n' in gct_obj:
                # Handle Python2 implementation of strings vs unicode
                if sys.version_info.major == 2:
                    gct_obj = unicode(gct_obj)

                # Wrap the raw data in a StringIO (file-like object)
                gct_io = io.StringIO(gct_obj)

            # Check to see if the string contains a URL
            # Skip if a file-like object has already been obtained
            if self._is_url(gct_obj) and gct_io is None:
                gct_io = urllib2.urlopen(gct_obj)

            # Otherwise try treating the string as a file path
            # If this doesn't work throw an error, we don't know what to do with this string.
            # Skip if a file-like object has already been obtained
            if gct_io is None:
                try:
                    # Point gct_obj to file (read in the code below)
                    gct_io = open(gct_obj, 'r')
                except IOError:
                    raise IOError('Input string not determined to be raw data, URL or readable file.')

        # If we still don't have a file-like object at this point, throw an error
        if gct_io is None:
            raise TypeError('Unknown type passed to GCT()')

        # Load the GCT file into a DataFrame
        self.dataframe = pandas.read_csv(gct_io, sep='\t', header=2, index_col=[0, 1], skip_blank_lines=True)

    @staticmethod
    def _is_url(url):
        """
        Used to determine if a given string represents a URL
        """
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if regex.match(url) is not None:
            return True
        else:
            return False

    def _repr_html_(self):
        """
        Return a html representation for a particular DataFrame.
        Mainly for Jupyter notebook.
        """
        return self.dataframe._repr_html_()

    def row_count(self):
        """
        Return the number of data rows in the GCT file
        """
        return len(self.dataframe.index)

    def col_count(self):
        """
        Return the number of data columns in the GCT file
        """
        return len(self.dataframe.columns)


class ODF(object):
    """
    Wraps and represents an ODF file, importing the associated data
    into a pandas dataframe.

    For more information on the ODF format see:
    http://software.broadinstitute.org/cancer/software/genepattern/file-formats-guide

    :odf_obj: The ODF file. Accepts a file-like object, a file path, a URL to the file
              or a string containing the raw data.
    """
    dataframe = None
    headers = None
    model = None

    def __init__(self, odf_obj):
        """
        Create a wrapper object for the ODF file
        """
        odf_io = None

        # Ensure that the user has pandas installed
        try:
            import pandas
        except ImportError:
            raise ImportError('pandas is required to work with a ODF file in a DataFrame.' +
                              ' Try: pip install pandas')

        # Check to see if odf_io if a GPFile object from the GenePattern Python Client, if installed
        try:
            import gp
            if isinstance(odf_obj, gp.GPFile):
                odf_io = odf_obj.open()
        except ImportError:
            pass

        # Check to see if odf_obj is a file-like object
        # Skip if a file-like object has already been obtained
        if hasattr(odf_obj, 'read') and odf_io is None:
            odf_io = odf_obj

        # Check to see if odf_obj is a string
        # Skip if a file-like object has already been obtained
        if isinstance(odf_obj, str) and odf_io is None:

            # Check to see if the string contains multiple lines
            # If it does, it is likely raw data
            if '\n' in odf_obj:
                # Handle Python2 implementation of strings vs unicode
                if sys.version_info.major == 2:
                    odf_obj = unicode(odf_obj)

                # Wrap the raw data in a StringIO (file-like object)
                odf_io = io.StringIO(odf_obj)

            # Check to see if the string contains a URL
            # Skip if a file-like object has already been obtained
            if self._is_url(odf_obj) and odf_io is None:
                odf_io = urllib2.urlopen(odf_obj)

            # Otherwise try treating the string as a file path
            # If this doesn't work throw an error, we don't know what to do with this string.
            # Skip if a file-like object has already been obtained
            if odf_io is None:
                try:
                    # Point odf_obj to file (read in the code below)
                    odf_io = open(odf_obj, 'r')
                except IOError:
                    raise IOError('Input string not determined to be raw data, URL or readable file.')

        # If we still don't have a file-like object at this point, throw an error
        if odf_io is None:
            raise TypeError('Unknown type passed to ODF()')

        # Read the file as an array of lines
        raw_lines = odf_io.readlines()

        try:
            # Read the header count
            header_count = self._extract_header_number(raw_lines)

            # Read the header dict
            self.headers = self._parse_header(raw_lines)

            # Read the model
            self.model = self._extract_model(self.headers)

            # Read the column names
            column_names = self._extract_column_names(self.headers)

            # Assemble the data
            data_lines = self._join_data_lines(raw_lines, header_count)

            # Put together new IO
            odf_string_io = io.StringIO(data_lines)

            # Load the ODF file into a DataFrame
            self.dataframe = pandas.read_csv(odf_string_io, sep='\t', header=None, names=column_names, skip_blank_lines=True)

        # Catch any errors related to parsing the ODF file
        except Exception:
            raise TypeError('Error parsing ODF file')

    @staticmethod
    def _is_url(url):
        """
        Used to determine if a given string represents a URL
        """
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if regex.match(url) is not None:
            return True
        else:
            return False

    def _repr_html_(self):
        """
        Return a html representation for a particular DataFrame.
        Mainly for Jupyter notebook.
        """
        return self.dataframe._repr_html_()

    @staticmethod
    def _extract_header_value(line):
        """
        Extracts a key / value pair from a header line in an ODF file
        """
        line = line.decode("UTF-8").strip()

        # Skip blank lines, returning None
        if not line:
            return None

        # Attempt to split by equals sign
        halves = line.split('=')
        if len(halves) > 1:
            key = halves[0].strip()
            value = halves[1].strip()
            return {key: value}

        # Otherwise, attempt to split by colon
        else:
            halves = line.split(':')
            key = halves[0].strip()
            value = halves[1].strip()
            return {key: value}

    def _extract_header_number(self, lines):
        """
        Extracts the number of header lines from the second line of the ODF file
        """
        pair = self._extract_header_value(lines[1])
        value_list = list(pair.values())
        return int(value_list[0])

    def _parse_header(self, lines):
        """
        Parse the ODF header and return a dict of all key / value pairs
        """
        header_count = self._extract_header_number(lines)
        header_dict = {}
        for i in range(2, header_count + 2):
            pair = self._extract_header_value(lines[i])

            if not pair:  # Ignore empty strings
                continue

            header_dict.update(pair)
        return header_dict

    @staticmethod
    def _extract_column_names(headers):
        """
        Return an array containing the column names, extracted from the headers
        """
        name_string = headers['COLUMN_NAMES']
        return name_string.split('\t')

    @staticmethod
    def _extract_model(headers):
        """
        Return an array containing the column names, extracted from the headers
        """
        return headers['Model']

    def count_header_blanks(self, lines, count):
        """
        Count the number of blank lines in the header
        """
        blanks = 0
        for i in range(2, count + 2):
            pair = self._extract_header_value(lines[i])
            if not pair:
                blanks += 1
        return blanks

    def _join_data_lines(self, lines, skip):
        """
        Join all the data lines into a byte string
        """
        blank_lines = self.count_header_blanks(lines, skip)
        body = lines[skip + blank_lines + 2:]
        return b''.join(body).decode('UTF-8')

    def row_count(self):
        """
        Return the number of data rows in the ODF file
        """
        return len(self.dataframe.index)

    def col_count(self):
        """
        Return the number of data columns in the ODF file
        """
        return len(self.dataframe.columns)
