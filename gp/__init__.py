import warnings

"""
GenePattern Python Client

Compatible with Python 3.4+
"""

__authors__ = ['Thorin Tabor', 'Chet Birger']
__copyright__ = 'Copyright 2014-2019, Regents of the University of California & Broad Institute'
__version__ = '1.4.5.post1'
__status__ = 'Production'

# Import core functionality
from .core import GPException, GPFile, GPJob, GPJobSpec, GPResource, GPServer, GPTask, GPTaskParam, GPJSONEncoder

# Import subpackages, if available
try:
    import gp.utils
except Exception:
    # Ignore if subpackages are unavailable
    True

# # Warn if this is imported using the old `gp` namespace
# if __name__ == 'gp':
#     message = 'The GenePattern Python library has been restructured and now uses the `genepattern.client` package name. ' + \
#               'Please import using that name as `gp` will be deprecated in the future'
#     warnings.warn(message, PendingDeprecationWarning)
#     print('WARNING: ' + message)
