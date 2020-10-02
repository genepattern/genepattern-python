import warnings

"""
GenePattern Python Client

Compatible with Python 3.6+
"""

__authors__ = ['Thorin Tabor', 'Chet Birger']
__copyright__ = 'Copyright 2014-2020, Regents of the University of California & Broad Institute'
__version__ = '20.10'
__status__ = 'Production'

# Import core functionality
from .core import GPException, GPFile, GPJob, GPJobSpec, GPResource, GPServer, GPTask, GPTaskParam, GPJSONEncoder

# Import subpackages, if available
try:
    import gp.utils
except Exception:
    # Ignore if subpackages are unavailable
    True

