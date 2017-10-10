#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ged4py.detail.name` module."""

import unittest

from ged4py.detail.name import split_name


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
