"""
Tests for loading GCT and ODF files into pandas dataframes
"""


from .. import gp


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
    assert True


def test_odf_load_file():
    assert True


def test_odf_load_url():
    odf = gp.data.ODF('https://software.broadinstitute.org/cancer/software/genepattern/data/protocols/all_aml_test.preprocessed.comp.marker.odf')
    odf_asserts(odf)


def test_odf_load_path():
    assert True


def test_odf_load_string():
    assert True


def odf_asserts(odf):
    assert odf.model is not None
    assert odf.headers is not None
