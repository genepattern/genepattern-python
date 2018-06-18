from distutils.core import setup


# Read version and other metadata from file
__version__ = '1.5.0.RC4'

setup(
    name='genepattern-python',
    packages=['gp'],
    version=__version__,
    description='Library for programmatically interacting with GenePattern from Python.',
    author='Thorin Tabor',
    author_email='tmtabor@cloud.ucsd.edu',
    url='https://github.com/genepattern/genepattern-python',
    download_url='https://github.com/genepattern/genepattern-python/archive/' + __version__ + '.tar.gz',
    keywords=['genepattern', 'genomics', 'bioinformatics'],
    license='BSD'
)
