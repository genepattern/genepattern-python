import warnings

"""
GenePattern Python Client

Compatible with Python 3.6+
"""

__authors__ = ['Thorin Tabor', 'Chet Birger']
__copyright__ = 'Copyright 2014-2022, Regents of the University of California & Broad Institute'
__version__ = '22.10'
__status__ = 'Production'

# Import core functionality
from .core import GPException, GPFile, GPJob, GPJobSpec, GPResource, GPServer, GPTask, GPTaskParam, GPJSONEncoder
