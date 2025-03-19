"""Top-level package for GEDCOM parser for Python.

Most of the code in the s package is located in individual modules:

- :py:mod:`ged4py.parser` - defines :py:class:`~ged4py.parser.GedcomReader`
  class which is the main entry point for the whole package;
- :py:mod:`ged4py.model` - collection of classes constituting ``ged4py`` data
  model;
- :py:mod:`ged4py.calendar` - classes for working with calendar dates;
- :py:mod:`ged4py.date` - parsing and handling of GEDCOM dates;
- :py:mod:`ged4py.detail` - few modules for implementation details.

:py:class:`~ged4py.parser.GedcomReader` class can be imported directly from
top-level package as::

    from ged4py import GedcomReader

"""

# register ansel encoding
import ansel as _ansel

from .parser import GedcomReader  # noqa: F401

_ansel.register()

__author__ = "Andy Salnikov"
__email__ = "ged4py@py-dev.com"
__version__ = "0.5.2"
