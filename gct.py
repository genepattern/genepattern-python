__authors__ = ['Thorin Tabor']
__copyright__ = 'Copyright 2016, Broad Institute'
__version__ = '0.1.0'
__status__ = 'Beta'

"""
GCT Tools

Tools for loading a GCT file and working with its contents as a Pandas DataFrame.
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
