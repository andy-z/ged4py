# -*- coding: utf-8 -*-

"""Top-level package for GEDCOM parser for Python."""

__author__ = """Andy Salnikov"""
__email__ = 'ged4py@py-dev.com'
__version__ = '0.1.4'

from . import codecs  # noqa: F401, needed to register ANSEL codec
from .parser import GedcomReader  # noqa: F401
