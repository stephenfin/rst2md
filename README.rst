======
rst2md
======

A utility and library to convert a reStructuredText document to Markdown.

.. note::

   This has been tested on a number of documents, but as of yet no test suite exists so it is likely
   incomplete.

.. note::

   Only plain reStructuredText documents are supported. There is no support for Sphinx extensions or
   similar.

Installation
------------

.. code-block::

    pip install --user rst2md

Usage
-----

This can be used as a library or from the command line.

As a library:

.. code-block:: python

    import pathlib
    from rst2md import convert_rst_to_md

    path = pathlib.Path('README.rst')
    with path.open('r') as f:
        data = f.read()

    md = convert_rst_to_md(path.name, data)

From the command line:

.. code-block:: bash

    python -m rst2md README.rst
