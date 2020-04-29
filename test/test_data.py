"""
Tests for loading GCT and ODF files into pandas dataframes
"""
import pytest

import gp
import gp.data
import urllib.request


@pytest.fixture(scope="session", autouse=True)
def before_tests(request):
    # Download files for local use
    urllib.request.urlretrieve("https://datasets.genepattern.org/data/all_aml/all_aml_test.gct", "all_aml_test.gct")
    urllib.request.urlretrieve("https://datasets.genepattern.org/data/all_aml/all_aml_test.preprocessed.comp.marker.odf",
                               "all_aml_test.preprocessed.comp.marker.odf")

    # Clean up after ourselves
    request.addfinalizer(after_tests)


def test_gct_load_gpfile():
    gpfile = gp.GPFile(gp.GPServer('http://genepattern.broadinstitute.org/gp', '', ''),
                       'https://datasets.genepattern.org/data/all_aml/all_aml_test.gct')
    gct = gp.data.GCT(gpfile)
    gct_asserts(gct)


def test_gct_load_file():
    file = open('all_aml_test.gct', 'r')
    gct = gp.data.GCT(file)
    gct_asserts(gct)


def test_gct_load_url():
    gct = gp.data.GCT('https://datasets.genepattern.org/data/all_aml/all_aml_test.gct')
    gct_asserts(gct)


def test_gct_load_path():
    gct = gp.data.GCT('all_aml_test.gct')
    gct_asserts(gct)


def test_gct_load_string():
    with open('all_aml_test.gct', 'r') as file:
        file_str = file.read()
    gct = gp.data.GCT(file_str)
    gct_asserts(gct)


def test_odf_load_gpfile():
    gpfile = gp.GPFile(gp.GPServer('http://genepattern.broadinstitute.org/gp', '', ''),
                       'https://datasets.genepattern.org/data/all_aml/all_aml_test.preprocessed.comp.marker.odf')
    odf = gp.data.ODF(gpfile)
    odf_asserts(odf)


def test_odf_load_file():
    file = open('all_aml_test.preprocessed.comp.marker.odf', 'r')
    odf = gp.data.ODF(file)
    odf_asserts(odf)


def test_odf_load_url():
    odf = gp.data.ODF('https://datasets.genepattern.org/data/all_aml/all_aml_test.preprocessed.comp.marker.odf')
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


def gct_asserts(odf):
    assert odf.row_count()
    assert odf.col_count()


def odf_asserts(odf):
    assert odf.model is not None
    assert odf.headers is not None
    assert odf.row_count()
    assert odf.col_count()
