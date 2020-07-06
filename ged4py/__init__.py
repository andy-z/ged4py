# -*- coding: utf-8 -*-

"""Top-level package for GEDCOM parser for Python."""

from .parser import GedcomReader  # noqa: F401

# register ansel encoding
import ansel as _ansel
_ansel.register()

__author__ = """Andy Salnikov"""
__email__ = 'ged4py@py-dev.com'
__version__ = '0.2.0'
