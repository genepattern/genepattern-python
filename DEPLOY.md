# How to Deploy to PyPi Test

1. Make sure setup.py and gp.py/__version__ are updated
2. cd to *genepattern-python* directory
3. Upload via *python setup.py sdist upload -r pypitest*
4. If the upload fails go to https://testpypi.python.org/pypi and manually upload dist/genepattern-python-*.tar.gz
5. Test the deploy by uninstalling and reinstalling the package: *sudo pip uninstall genepattern-python* and *sudo pip install --index-url https://test.pypi.org/simple/ genepattern-python* .

# How to Deploy to Production PyPi

1. First deploy to test and ensure everything is working correctly (see above).
2. cd to *genepattern-python* directory
3. Upload via python setup.py sdist bdist_wheel; twine upload dist/*
4. If the upload fails go to https://pypi.python.org/pypi and manually upload dist/genepattern-python-*.tar.gz
5. Test the deploy by uninstalling and reinstalling the package: *sudo pip uninstall genepattern-python* and *sudo pip install genepattern-python* .

# How to Deploy to Conda

1. Deploy to Production PyPi
2. Navigate to Anaconda directory
> cd anaconda
3. Run the following, removing the existing directory if necessary:
> conda skeleton pypi genepattern-python --version XXX
4. Build the package:
> conda build genepattern-python
5. Upload the newly built package:
> anaconda upload /Users/tabor/anaconda/conda-bld/osx-64/genepattern-python-XXX-py35_0.tar.bz2 -u genepattern
6. Converting this package to builds for other operating systems can be done as shown below. You will need to upload each
built version using a separate upload command.
> conda convert --platform all /Users/tabor/anaconda/conda-bld/osx-64/genepattern-python-XXX-py35_0.tar.bz2 -o conda-bld/
7. Log into the [Anaconda website](https://anaconda.org/) to make sure everything is good.