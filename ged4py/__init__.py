# -*- coding: utf-8 -*-

"""Top-level package for GEDCOM parser for Python."""

__author__ = """Andy Salnikov"""
__email__ = 'ged4py@py-dev.com'
__version__ = '0.1.13'

import ansel as _ansel
_ansel.register()

from .parser import GedcomReader  # noqa: F401
