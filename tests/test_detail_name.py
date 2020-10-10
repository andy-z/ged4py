#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ged4py.detail.name` module."""

import unittest

from ged4py.detail.name import (split_name, parse_name_altree,
                                parse_name_myher, parse_name_ancestris)
from ged4py import model


class TestDetailName(unittest.TestCase):
    """Tests for `ged4py.detail.io` module."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_001_split_name(self):
        """Test detail.name.split_name()."""

        nsplit = split_name("First Name Only")
        self.assertEqual(nsplit, ("First Name Only", "", ""))

        nsplit = split_name("First Name /Last Name/")
        self.assertEqual(nsplit, ("First Name", "Last Name", ""))

        nsplit = split_name("First/ Last / ")
        self.assertEqual(nsplit, ("First", "Last", ""))

        nsplit = split_name(" First /Last ")
        self.assertEqual(nsplit, ("First", "Last", ""))

        nsplit = split_name("First /Last/ II ")
        self.assertEqual(nsplit, ("First", "Last", "II"))

        nsplit = split_name("/Last/ Karl II")
        self.assertEqual(nsplit, ("", "Last", "Karl II"))

        nsplit = split_name("Жанна /Иванова (Д'Арк)/")
        self.assertEqual(nsplit, ("Жанна", "Иванова (Д'Арк)", ""))

    def test_002_parse_name_altree(self):
        """Test parse_name_altree()
        """
        rec = model.NameRec()
        rec.level = 1
        rec.tag = "NAME"
        rec.dialect = model.Dialect.ALTREE

        rec.value = "First /Last Name/ Second"
        name_tup = parse_name_altree(rec)
        self.assertIsInstance(name_tup, tuple)
        self.assertEqual(name_tup, ("First", "Last Name", "Second"))

        rec.value = "First /Last(-er)/ Second"
        name_tup = parse_name_altree(rec)
        self.assertIsInstance(name_tup, tuple)
        self.assertEqual(name_tup, ("First", "Last(-er)", "Second"))

        rec.value = "First /Last (-er)/ Second"
        name_tup = parse_name_altree(rec)
        self.assertIsInstance(name_tup, tuple)
        self.assertEqual(name_tup, ("First", "Last (-er)", "Second"))

        maiden = model.Record()
        maiden.level = 2
        maiden.tag = "SURN"
        maiden.value = "Maiden"
        rec.value = "First /Last (Maiden)/"
        rec.sub_records = [maiden]
        name_tup = parse_name_altree(rec)
        self.assertIsInstance(name_tup, tuple)
        self.assertEqual(name_tup, ("First", "Last", "", "Maiden"))

    def test_003_parse_name_myher(self):
        """Test parse_name_myher()
        """
        rec = model.NameRec()
        rec.level = 1
        rec.tag = "NAME"
        rec.dialect = model.Dialect.MYHERITAGE

        rec.value = "First /Last Name/ Second"
        name_tup = parse_name_myher(rec)
        self.assertIsInstance(name_tup, tuple)
        self.assertEqual(name_tup, ("First", "Last Name", "Second"))

        rec.value = "First /Last(-er)/ Second"
        name_tup = parse_name_myher(rec)
        self.assertIsInstance(name_tup, tuple)
        self.assertEqual(name_tup, ("First", "Last(-er)", "Second"))

        rec.value = "First /Last (-er)/ Second"
        name_tup = parse_name_altree(rec)
        self.assertIsInstance(name_tup, tuple)
        self.assertEqual(name_tup, ("First", "Last (-er)", "Second"))

        married = model.Record()
        married.level = 2
        married.tag = "_MARNM"
        married.value = "Married"
        rec.value = "First /Maiden/"
        rec.sub_records = [married]
        name_tup = parse_name_myher(rec)
        self.assertIsInstance(name_tup, tuple)
        self.assertEqual(name_tup, ("First", "Married", "", "Maiden"))

    def test_004_parse_name_ancestris(self):
        """Test parse_name_ancestris()

        Ancestris dialect is just a split_name() which is tested separately,
        so the is not much testing needed for it.
        """
        rec = model.NameRec()
        rec.level = 1
        rec.tag = "NAME"
        rec.dialect = model.Dialect.ANCESTRIS

        rec.value = "First /Last Name/ Second"
        name_tup = parse_name_ancestris(rec)
        self.assertIsInstance(name_tup, tuple)
        self.assertEqual(name_tup, ("First", "Last Name", "Second"))

        rec.value = "First /Last(-er)/ Second"
        name_tup = parse_name_ancestris(rec)
        self.assertIsInstance(name_tup, tuple)
        self.assertEqual(name_tup, ("First", "Last(-er)", "Second"))

        rec.value = "First /Last (-er)/ Second"
        name_tup = parse_name_ancestris(rec)
        self.assertIsInstance(name_tup, tuple)
        self.assertEqual(name_tup, ("First", "Last (-er)", "Second"))
