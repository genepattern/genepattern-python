"""
Tests for loading GCT and ODF files into pandas dataframes
"""
import pytest

import gp
import gp.data
import sys

# Imports requiring compatibility between Python 2 and Python 3
if sys.version_info.major == 2:
    import urllib2
else:
    import urllib.request as urllib2


@pytest.fixture(scope="session", autouse=True)
def before_tests(request):
    # Download files for local use
    urllib2.request.urlretrieve("https://software.broadinstitute.org/cancer/software/genepattern/data/protocols/all_aml_test.preprocessed.comp.marker.odf",
                               "all_aml_test.preprocessed.comp.marker.odf")

    # Clean up after ourselves
    request.addfinalizer(after_tests)


def test_gct_load_gpfile():
    assert True


def test_gct_load_file():
    assert True


def test_gct_load_url():
    assert True


def test_gct_load_path():
    assert True


def test_gct_load_string():
    assert True


def test_odf_load_gpfile():
    gpfile = gp.GPFile(gp.GPServer('http://genepattern.broadinstitute.org/gp', '', ''),
                       'https://software.broadinstitute.org/cancer/software/genepattern/data/protocols/all_aml_test.preprocessed.comp.marker.odf')
    odf = gp.data.ODF(gpfile)
    odf_asserts(odf)


def test_odf_load_file():
    file = open('all_aml_test.preprocessed.comp.marker.odf', 'r')
    odf = gp.data.ODF(file)
    odf_asserts(odf)


def test_odf_load_url():
    odf = gp.data.ODF('https://software.broadinstitute.org/cancer/software/genepattern/data/protocols/all_aml_test.preprocessed.comp.marker.odf')
    odf_asserts(odf)


def test_odf_load_path():
    odf = gp.data.ODF('all_aml_test.preprocessed.comp.marker.odf')
    odf_asserts(odf)


def test_odf_load_string():
    with open('all_aml_test.preprocessed.comp.marker.odf', 'r') as file:
        file_str = file.read()
    odf = gp.data.ODF(file_str)
    odf_asserts(odf)


def after_tests():
    pass


#####################
# Utility functions #
#####################


def odf_asserts(odf):
    assert odf.model is not None
    assert odf.headers is not None
    assert odf.row_count()
    assert odf.col_count()
