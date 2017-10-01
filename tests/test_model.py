#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ged4py.model` module."""

import unittest

from ged4py import model


class TestModel(unittest.TestCase):
    """Tests for `ged4py.model` module."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_001_record(self):
        """Test Record class."""

        rec = model.Record()
        self.assertEqual(vars(rec), {'dialect': None,
                                     'xref_id': None,
                                     'level': None,
                                     'value': None,
                                     'tag': None,
                                     'sub_records': None,
                                     'offset': None})

        rec.level = 0
        rec.xref_id = "@x@"
        rec.tag = "REC"
        rec.value = "value"
        rec.sub_records = []
        rec.offset = 1000
        rec.dialect = model.DIALECT_DEFAULT

        rec.freeze()
        self.assertTrue(rec.sub_tag("SUB") is None)
        self.assertEqual(rec.sub_tags("SUB"), [])

    def test_002_record_sub(self):
        """Test Record class with sub-records."""

        rec = model.Record()
        rec.level = 0
        rec.xref_id = "@x@"
        rec.tag = "REC"
        rec.value = "value"
        rec.sub_records = []
        rec.offset = 1000
        rec.dialect = model.DIALECT_DEFAULT

        for subtag in ['SUBA', 'SUBB', 'SUBC']:
            for i in range(3):

                sub = model.Record()

                sub.level = 1
                sub.tag = subtag
                sub.value = i
                sub.sub_records = []
                sub.offset = 1100 + 100 * i
                sub.dialect = model.DIALECT_DEFAULT
                sub.freeze()

                rec.sub_records.append(sub)

        rec.freeze()
        for subtag in ['SUBA', 'SUBB', 'SUBC']:
            self.assertEqual(rec.sub_tag(subtag).tag, subtag)
            self.assertEqual(len(rec.sub_tags(subtag)), 3)
        self.assertTrue(rec.sub_tag("SUB") is None)
        self.assertEqual(rec.sub_tags("SUB"), [])

    def test_010_name_default(self):
        """Test Name class with default dialect."""

        rec = model.Name()
        rec.level = 1
        rec.tag = "NAME"
        rec.dialect = model.DIALECT_DEFAULT

        rec.value = ""
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("", "", ""))

        rec.value = "First Name"
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("First Name", "", ""))

        rec.value = " /Last Name/ "
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("", "Last Name", ""))

        rec.value = " /Last Name"
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("", "Last Name", ""))

        rec.value = "First /Last Name/ "
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("First", "Last Name", ""))

        rec.value = "First /Last Name/ Second "
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("First", "Last Name", "Second"))

        rec.value = "First /Last (Maiden)/"
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("First", "Last (Maiden)", ""))

    def test_011_name_altree(self):
        """Test Name class with ALTREE dialect."""

        rec = model.Name()
        rec.level = 1
        rec.tag = "NAME"
        rec.dialect = model.DIALECT_ALTREE

        rec.value = ""
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("", "", ""))

        rec.value = "First /Last Name/ Second "
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("First", "Last Name", "Second"))

        rec.value = "First /Last (Maiden)/"
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("First", "Last", "", "Maiden"))

    def test_012_name_myher(self):
        """Test Name class with MYHERITAGE dialect."""

        rec = model.Name()
        rec.level = 1
        rec.tag = "NAME"
        rec.dialect = model.DIALECT_MYHERITAGE
        rec.sub_records = []

        rec.value = ""
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("", "", ""))

        rec.value = "First /Last Name/ Second "
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("First", "Last Name", "Second"))

        married = model.Record()
        married.level = 2
        married.tag = "_MARNM"
        married.value = "Last"
        married.sub_records = []
        rec.value = "First /Maiden/"
        rec.sub_records = [married]
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("First", "Last", "", "Maiden"))


    def test_900_make_record(self):
        """Test make_record method()"""

        rec = model.make_record(0, "@xref@", "TAG", "value", [], 1000,
                                model.DIALECT_DEFAULT)
        rec.freeze()
        self.assertTrue(type(rec) is model.Record)
        self.assertEqual(rec.level, 0)
        self.assertEqual(rec.xref_id, "@xref@")
        self.assertEqual(rec.tag, "TAG")
        self.assertEqual(rec.value, "value")
        self.assertEqual(rec.sub_records, [])
        self.assertEqual(rec.offset, 1000)
        self.assertEqual(rec.dialect, model.DIALECT_DEFAULT)

        rec = model.make_record(1, None, "NAME", "Joe", [], 1000,
                                model.DIALECT_ALTREE)
        rec.freeze()
        self.assertTrue(type(rec) is model.Name)
        self.assertEqual(rec.level, 1)
        self.assertTrue(rec.xref_id is None)
        self.assertEqual(rec.tag, "NAME")
        self.assertEqual(rec.value, ("Joe", "", ""))
        self.assertEqual(rec.sub_records, [])
        self.assertEqual(rec.offset, 1000)
        self.assertEqual(rec.dialect, model.DIALECT_ALTREE)

        rec = model.make_record(0, "@I1@", "INDI", None, [], 1000,
                                model.DIALECT_MYHERITAGE)
        rec.freeze()
        self.assertTrue(type(rec) is model.Individual)
        self.assertEqual(rec.level, 0)
        self.assertEqual(rec.xref_id, "@I1@")
        self.assertEqual(rec.tag, "INDI")
        self.assertTrue(rec.value is None)
        self.assertEqual(rec.sub_records, [])
        self.assertEqual(rec.offset, 1000)
        self.assertEqual(rec.dialect, model.DIALECT_MYHERITAGE)
