[![Version](https://img.shields.io/pypi/v/genepattern-python.svg)](https://pypi.python.org/pypi/genepattern-python)
[![Build](https://travis-ci.org/genepattern/genepattern-python.svg?branch=master)](https://travis-ci.org/genepattern/genepattern-python.svg?branch=master)
[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg?style=flat)](https://github.com/genepattern/example-notebooks/blob/master/GenePattern%20Python%20Tutorial.ipynb)

# GenePattern Python Library

This is a Python library for working with GenePattern programmatically. Calls from this library execute the GenePattern REST API.

## Supported Versions

This library supports Python 2.7 and Python 3.3+. The bundled data submodule `gp.data` requires [pandas](http://pandas.pydata.org/), although the rest of the features do not.

## Installing

It is recommended to install this library from PIP. Simply execute the command below:

> sudo pip install genepattern-python

## Upgrading

To upgrade to the latest version of the library, execute the command below:

> sudo pip install genepattern-python --upgrade

## Tutorial

A tutorial on how to use the GenePattern Python Library is [available here](https://github.com/genepattern/example-notebooks/blob/master/GenePattern%20Python%20Tutorial.ipynb).

## "Connection Reset by Peer" Error

Connecting to the GenePattern public server now requires TLS 1.2+. Older versions of SSL and TLS will no longer work. If you're attempting to connect and receiving a "Connection Reset by Peer" error, you will need to update the OpenSSL library associated with your Python installation.
