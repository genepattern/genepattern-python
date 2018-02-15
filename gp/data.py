__authors__ = ['Thorin Tabor']
__copyright__ = 'Copyright 2016, Broad Institute'
__version__ = '0.1.1'
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

############################
# Shared Utility Functions #
############################


def write_odf(df, file_path, headers=None):
    """
    Writes the provided DataFrame to a ODF file.

    Assumes that the DataFrame matches the structure of those produced
    by the ODF() function in this library

    :param df: the DataFrame to write to ODF
    :param file_path: path to which to write the ODF file
    :param headers: A dict of ODF headers, if none are provided will attempt to read them from the ODF file
    :return:
    """
    if headers is None and hasattr(df, 'headers'):
        headers = df.headers
    else:
        raise AttributeError('ODF headers not provided')

    with open(file_path, 'w') as file:
        file.write(_header_dict_to_str(headers))
        df.to_csv(file, sep='\t', header=False, index=False, mode='w+')


def write_gct(df, file_path):
    """
    Writes the provided DataFrame to a GCT file.

    Assumes that the DataFrame matches the structure of those produced
    by the GCT() function in this library

    :param df:
    :param file_path:
    :return:
    """
    with open(file_path, 'w') as file:
        file.write('#1.2\n' + str(len(df.index)) + '\t' + str(len(df.columns)) + '\n')
        df.to_csv(file, sep='\t', mode='w+')


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


#########################
# ODF Utility Functions #
#########################


def _header_dict_to_str(headers):
    # Define the list of headers to handle as special cases
    special = ['HeaderLines', 'COLUMN_NAMES', 'COLUMN_TYPES', 'Model', 'DataLines']

    # Add the initial ODF version line
    combined = 'ODF 1.0\n'

    # Add HeaderLines
    combined += 'HeaderLines=' + str(len(headers)) + '\n'

    # Add column names, if available
    if 'COLUMN_NAMES' in headers:
        combined += 'COLUMN_NAMES:' + str(headers['COLUMN_NAMES']) + '\n'

    # Add column types, if available
    if 'COLUMN_TYPES' in headers:
        combined += 'COLUMN_TYPES:' + str(headers['COLUMN_TYPES']) + '\n'

    # Add model, if available
    if 'Model' in headers:
        combined += 'Model=' + str(headers['Model']) + '\n'

    # Add remaining headers
    for key, value in sorted(headers.items()):
        if key not in special:
            combined += str(key) + '=' + str(value) + '\n'

    # Add data lines, if available
    if 'DataLines' in headers:
        combined += 'DataLines=' + str(headers['DataLines']) + '\n'

    # Return the combined header string
    return combined


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


# --- This block was added by Edwin Juarez on 2018-01-26 --- #

def minimumEditDistance(s1, s2):
    """
    This function computes a distance between two stings
    From: https://rosettacode.org/wiki/Levenshtein_distance#Python
    """
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    distances = range(len(s1) + 1)
    for index2, char2 in enumerate(s2):
        newDistances = [index2 + 1]
        for index1, char1 in enumerate(s1):
            if char1 == char2:
                newDistances.append(distances[index1])
            else:
                newDistances.append(1 + min((distances[index1],
                                             distances[index1 + 1],
                                             newDistances[-1])))
        distances = newDistances
    return distances[-1]


def extract_classes(list_of_strings, number_of_classes=2, affinity='euclidean'):
    """
    This function will apply clustering to get representative classes
    and will return a list/array with numeric identifiers for each sample.
    Adapted from here:
    https://stats.stackexchange.com/questions/123060/clustering-a-long-list-of-strings-words-into-similarity-groups
    """
    import numpy as np
    import sklearn.cluster

    words = np.asarray(list_of_strings)  # So that indexing with a list will work
    lev_similarity = -1 * np.array([[minimumEditDistance(w1, w2) for w1 in words] for w2 in words])
    affprop = sklearn.cluster.AffinityPropagation(affinity="precomputed", damping=0.5)
    affprop.fit(lev_similarity)
    list_of_numbers = np.array(affprop.labels_)
    return list_of_numbers.astype('str')


def assign_label(sample, classes, case_sensitive):
    """
    This simplistic function will go through each class in order,
    it stops once it finds a class which is contained in the sample string.
    """
    label = '__no_class__'
    flag = 'go'
    for current_class in classes:
        if flag == 'go':
            if case_sensitive:
                if current_class in sample:
                    label = current_class
                    flag = 'stop'
            else:
                if current_class.lower() in sample.lower():
                    label = current_class.lower()
                    flag = 'stop'
    return label


def strlist2num(str_list):
    """
    Take a list of strings to correlative numbers
    """
    import numpy as np

    classes = np.unique(str_list)
    num_list = []
    #     print(classes)
    for current_string in str_list:
        num = 0
        flag = 'go'
        for current_class in classes:
            if flag == 'go':
                if current_class == current_string:
                    num_list.append(num)
                    flag = 'stop'
                num += 1
    return np.array(num_list)


def list2cls(input_list, name_of_out='output.cls', sep='\t'):
    """
    This function creates a CLS file from a list-like object
    Copied and modified from Cuzcatlan
    """
    import numpy as np

    cls = open(name_of_out, 'w')
    cls.write("{}{}{}{}1\n".format(len(input_list), sep, len(np.unique(input_list)), sep))
    cls.write("#{}{}\n".format(sep, sep.join(np.unique(input_list).astype(str))))
    num_list = strlist2num(input_list)
    cls.write(sep.join(num_list.astype(str)) + '\n')
    #     print(sep.join(input_list.astype(str)))
    #     print(num_list)
    cls.close()


def make_cls(df, name, classes=None, case_sensitive=False, sep='\t'):
    """
    This function creates a CLS file from the column names of a GCT file
    """
    import numpy as np

    if classes is None:
        classes = extract_classes(list(df.columns))

    labels = []
    for sample in list(df.columns):
        labels.append(assign_label(sample, classes, case_sensitive))

    # Now that we have a list of labels, we turn these into a numeric list:
    if not name.endswith('.cls'):
        name += '.cls'
    name = name.replace(' ', '_')  # Simple reformatting, in case there were any spaces
    list2cls(np.array(labels), name_of_out=name, sep=sep)

    return name

# --- End of block [2018-01-26] --- #
