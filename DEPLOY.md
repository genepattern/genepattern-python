# How to Deploy to PyPi Test

1. Make sure setup.py and gp.py/__version__ are updated
2. cd to *genepattern-python* directory
3. Remove any residual build artifacts from the last time nbtools was built. This step is not necessary the first time the package is built.
> rm dist/\*.tar.gz; rm dist/\*.whl
4. Build the sdist and wheel artifacts.
> python -m build .
5. Upload the files by running:
> twine upload -r pypitest dist/\*.tar.gz; twine upload -r pypitest dist/\*.whl
6. If the upload fails go to [https://testpypi.python.org/pypi](https://testpypi.python.org/pypi) and manually upload dist/nbtools-*.tar.gz.
7. Test the deploy by uninstalling and reinstalling the package: 
> pip uninstall genepattern-python;
> pip install -i https://test.pypi.org/simple/ genepattern-python
> 
# How to Deploy to Production PyPi

1. First deploy to test and ensure everything is working correctly (see above).
2. cd to *genepattern-python* directory
4. Remove any residual build artifacts from the last time nbtools was built. This step is not necessary the first time the package is built.
> rm dist/\*.tar.gz; rm dist/\*.whl
5. Build the sdist and wheel artifacts.
> python -m build .
6. Upload the files by running:
> twine upload dist/\*.tar.gz; twine upload dist/\*.whl
7. If the upload fails go to [https://testpypi.python.org/pypi](https://testpypi.python.org/pypi) and manually upload dist/nbtools-*.tar.gz.
8. Test the deploy by uninstalling and reinstalling the package: 
> pip uninstall genepattern-python;
> pip install genepattern-python
> 
# How to Deploy to Conda

1. Deploy to Production PyPi
2. Navigate to Anaconda directory
> cd ~/opt/anaconda3
3. Run the following, removing the existing directory if necessary:
> conda skeleton pypi genepattern-python --version XXX
4. Build the package:
> conda build genepattern-python
5. Converting this package to builds for other operating systems can be done as shown below. You will need to upload each
built version using a separate upload command.
> conda convert --platform all ./conda-bld/osx-64/genepattern-python-XXX-py37_0.tar.bz2 -o conda-bld/
6. Upload the newly built package:
> anaconda upload ./conda-bld/*/genepattern-python-XXX-py37_0.tar.bz2 -u genepattern
7. Log into the [Anaconda website](https://anaconda.org/) to make sure everything is good.