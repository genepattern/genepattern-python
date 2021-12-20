from setuptools import setup


# Read version and other metadata from file
__version__ = '21.12'

with open('README.md') as f:
    long_description = f.read()

setup(
    name='genepattern-python',
    packages=['gp'],
    version=__version__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    description='Library for programmatically interacting with GenePattern from Python.',
    author='Thorin Tabor',
    author_email='tmtabor@cloud.ucsd.edu',
    url='https://github.com/genepattern/genepattern-python',
    download_url='https://github.com/genepattern/genepattern-python/archive/' + __version__ + '.tar.gz',
    keywords=['genepattern', 'genomics', 'bioinformatics'],
    license='BSD'
)
