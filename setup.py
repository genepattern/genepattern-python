import genepattern.client
from distutils.core import setup

setup(
    name='genepattern-python',
    package_dir={'gp': 'genepattern/client', 'genepattern.client': 'genepattern/client'},
    packages=['gp', 'genepattern.client'],
    version=genepattern.client.__version__,
    description='Library for programmatically interacting with GenePattern from Python.',
    author='Thorin Tabor',
    author_email='tmtabor@cloud.ucsd.edu',
    url='https://github.com/genepattern/genepattern-python',
    download_url='https://github.com/genepattern/genepattern-python/archive/' + genepattern.client.__version__ + '.tar.gz',
    keywords=['genepattern', 'genomics', 'bioinformatics'],
    license='BSD'
)
