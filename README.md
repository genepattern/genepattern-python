[![Version](https://img.shields.io/pypi/v/genepattern-python.svg)](https://pypi.python.org/pypi/genepattern-python)
[![Build](https://travis-ci.org/genepattern/genepattern-python.svg?branch=master)](https://travis-ci.org/genepattern/genepattern-python)
[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg?style=flat)](https://github.com/genepattern/example-notebooks/blob/master/GenePattern%20Python%20Tutorial.ipynb)

# GenePattern Python Library

This is a Python library for working with GenePattern programmatically. Behind the scenes, calls from this library execute the GenePattern REST API.

## Supported Python Versions

This library requires Python 3.6+. The bundled data submodule `gp.data` also requires [pandas](http://pandas.pydata.org/), although the rest of the module does not.

**Python 2 Support:** Support for Python 2 was removed in version 1.4.0. Python 2 users should use version 1.3.1.

## Installing

It is recommended to install this library from PIP. Simply execute the command below:

> pip install genepattern-python

## Upgrading

To upgrade to the latest version of the library, execute the command below:

> pip install genepattern-python --upgrade

## Tutorial

A tutorial on how to use the GenePattern Python Library is [available here](https://github.com/genepattern/example-notebooks/blob/master/GenePattern%20Python%20Tutorial.ipynb).

## "Connection Reset by Peer" Error

Connecting to the GenePattern public server now requires TLS 1.2+. Older versions of SSL and TLS will no longer work. If you're attempting to connect and receiving a "Connection Reset by Peer" error, you will need to update the OpenSSL library associated with your Python installation.
