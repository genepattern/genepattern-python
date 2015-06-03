from distutils.core import setup

setup(
    name='genepattern-python',
    py_modules=['gp', 'gp_widgets', 'gp_magics'],
    version='1.0.5',
    description='Library for programmatically interacting with GenePattern from Python.',
    author='Thorin Tabor',
    author_email='tabor@broadinstitute.org',
    url='https://github.com/genepattern/genepattern-python',
    download_url='https://github.com/genepattern/genepattern-python/archive/1.0.5.tar.gz',
    keywords=['genepattern', 'genomics', 'bioinformatics'],
    classifiers=['Framework :: IPython'],
)
