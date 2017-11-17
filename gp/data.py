__authors__ = ['Thorin Tabor']
__copyright__ = 'Copyright 2016, Broad Institute'
__version__ = '0.1.0'
__status__ = 'Beta'

"""
GenePattern Data Tools

Tools for loading GenePattern data files (such as GCT or ODF files) and
working with their contents in a Pandas DataFrame.

Compatible with Python 3.4+
"""

import gp
import re
import io
import types
import pandas as pd
import urllib.request


def GCT(gct_obj):
    """
    Create a Dataframe with the contents of the GCT file
    """
    # Handle all the various initialization types and get an IO object
    gct_io = _obtain_io(gct_obj)

    # Load the GCT file into a DataFrame
    df = pd.read_csv(gct_io, sep='\t', header=2, index_col=[0, 1], skip_blank_lines=True)

    # Apply backwards compatible methods
    _apply_backwards_compatibility(df)

    # Return the Dataframe
    return df


def ODF(odf_obj):
    """
    Create a Dataframe with the contents of the ODF file

    For more information on the ODF format see:
    http://software.broadinstitute.org/cancer/software/genepattern/file-formats-guide

    :odf_obj: The ODF file. Accepts a file-like object, a file path, a URL to the file
              or a string containing the raw data.
    """

    # Handle all the various initialization types and get an IO object
    odf_io = _obtain_io(odf_obj)

    # Read the file as an array of lines
    raw_lines = odf_io.readlines()

    # Convert byte strings to unicode strings
    raw_lines = _bytes_to_str(raw_lines)

    try:
        # Read the header count
        header_count = _extract_header_number(raw_lines)

        # Read the header dict
        headers = _parse_header(raw_lines)

        # Read the model
        model = _extract_model(headers)

        # Read the column names, if available
        column_names = _extract_column_names(headers)

        # Assemble the data
        data_lines = _join_data_lines(raw_lines, header_count)

        # Put together new IO
        odf_string_io = io.StringIO(data_lines)

        # Load the ODF file into a DataFrame
        df = pd.read_csv(odf_string_io, sep='\t', header=None, names=column_names, skip_blank_lines=True)

        # Apply backwards compatible methods
        _apply_backwards_compatibility(df)

        # Apply ODF-specific properties
        _apply_odf_properties(df, headers, model)

        # Return the Dataframe
        return df

    # Catch any errors related to parsing the ODF file
    except Exception:
        raise TypeError('Error parsing ODF file')


#########################
# ODF Utility Functions #
#########################


def _apply_odf_properties(df, headers, model):
    """
    Attach properties to the Dataframe to carry along ODF metadata

    :param df: The dataframe to be modified
    :param headers: The ODF header lines
    :param model: The ODF model type
    """
    df.headers = headers
    df.model = model


def _bytes_to_str(lines):
    """
    Convert all lines from byte string to unicode string, if necessary
    """
    if len(lines) >= 1 and hasattr(lines[0], 'decode'):
        return [line.decode('utf-8') for line in lines]
    else:
        return lines


def _extract_header_value(line):
    """
    Extracts a key / value pair from a header line in an ODF file
    """

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


def _extract_column_names(headers):
    """
    Return an array containing the column names, extracted from the headers
    """
    if 'COLUMN_NAMES' in headers:
        name_string = headers['COLUMN_NAMES']
        return name_string.split('\t')
    else:
        return None


def _extract_model(headers):
    """
    Return an array containing the column names, extracted from the headers
    """
    return headers['Model']


def _extract_header_number(lines):
    """
    Extracts the number of header lines from the second line of the ODF file
    """
    pair = _extract_header_value(lines[1])
    value_list = list(pair.values())
    return int(value_list[0])


def _parse_header(lines):
    """
    Parse the ODF header and return a dict of all key / value pairs
    """
    header_count = _extract_header_number(lines)
    header_dict = {}
    for i in range(2, header_count + 2):
        pair = _extract_header_value(lines[i])

        if not pair:  # Ignore empty strings
            continue

        header_dict.update(pair)
    return header_dict


def count_header_blanks(lines, count):
    """
    Count the number of blank lines in the header
    """
    blanks = 0
    for i in range(2, count + 2):
        pair = _extract_header_value(lines[i])
        if not pair:
            blanks += 1
    return blanks


def _join_data_lines(lines, skip):
    """
    Join all the data lines into a byte string
    """
    lines = list(map(str.strip, lines))
    blank_lines = count_header_blanks(lines, skip)
    body = lines[skip + blank_lines + 2:]
    return '\n'.join(body)


############################
# Shared Utility Functions #
############################


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


def _apply_backwards_compatibility(df):
    """
    Attach properties to the Dataframe to make it backwards compatible with older versions of this library

    :param df: The dataframe to be modified
    """
    df.row_count = types.MethodType(lambda self: len(self.index), df)
    df.col_count = types.MethodType(lambda self: len(self.columns), df)
    df.dataframe = df


def _obtain_io(init_obj):
    io_obj = None

    # Check to see if init_obj is a GPFile object from the GenePattern Python Client
    if isinstance(init_obj, gp.GPFile):
        io_obj = init_obj.open()

    # Check to see if init_obj is a file-like object
    # Skip if a file-like object has already been obtained
    if hasattr(init_obj, 'read') and io_obj is None:
        io_obj = init_obj

    # Check to see if gct_obj is a string
    # Skip if a file-like object has already been obtained
    if isinstance(init_obj, str) and io_obj is None:

        # Check to see if the string contains multiple lines
        # If it does, it is likely raw data
        if '\n' in init_obj:
            # Wrap the raw data in a StringIO (file-like object)
            io_obj = io.StringIO(init_obj)

        # Check to see if the string contains a URL
        # Skip if a file-like object has already been obtained
        if _is_url(init_obj) and io_obj is None:
            io_obj = urllib.request.urlopen(init_obj)

        # Otherwise try treating the string as a file path
        # If this doesn't work throw an error, we don't know what to do with this string.
        # Skip if a file-like object has already been obtained
        if io_obj is None:
            try:
                # Point gct_obj to file (read in the code below)
                io_obj = open(init_obj, 'r')
            except IOError:
                raise IOError('Input string not determined to be raw data, URL or readable file.')

    # If we still don't have a file-like object at this point, throw an error
    if io_obj is None:
        raise TypeError('Unknown type passed to GCT() or ODF()')

    # Return the io_obj
    return io_obj
