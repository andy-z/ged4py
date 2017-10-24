#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ged4py.model` module."""

import unittest

from ged4py import model
from ged4py.detail.date import DateValue


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

    def test_010_namerec_default(self):
        """Test NameRec class with default dialect."""

        rec = model.NameRec()
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

    def test_011_namerec_altree(self):
        """Test NameRec class with ALTREE dialect."""

        rec = model.NameRec()
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

    def test_012_namerec_myher(self):
        """Test NameRec class with MYHERITAGE dialect."""

        rec = model.NameRec()
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

    def test_020_name_default(self):
        """Test Name class with DEFAULT dialect."""

        dialect = model.DIALECT_DEFAULT
        names = [model.make_record(1, None, "NAME", "John /Smith/", [], 0, dialect).freeze()]
        name = model.Name(names, dialect)

        self.assertTrue(name._primary is names[0])
        self.assertEqual(name.surname, "Smith")
        self.assertEqual(name.given, "John")
        self.assertTrue(name.maiden is None)

        self.assertEqual(name.order(model.ORDER_SURNAME_GIVEN), ("1Smith", "1John"))
        self.assertEqual(name.order(model.ORDER_GIVEN_SURNAME), ("1John", "1Smith"))
        self.assertEqual(name.order(model.ORDER_MAIDEN_GIVEN), ("1Smith", "1John"))
        self.assertEqual(name.order(model.ORDER_GIVEN_MAIDEN), ("1John", "1Smith"))

        self.assertEqual(name.format(model.FMT_DEFAULT), ("John Smith"))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST), ("John Smith"))
        self.assertEqual(name.format(model.FMT_SURNAME_FIRST), ("Smith John"))
        self.assertEqual(name.format(model.FMT_SURNAME_FIRST | model.FMT_COMMA), ("Smith, John"))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_COMMA), ("John Smith"))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_MAIDEN), ("John Smith"))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_MAIDEN_ONLY), ("John Smith"))

        names = [model.make_record(1, None, "NAME", "John", [], 0, dialect).freeze()]
        name = model.Name(names, dialect)

        self.assertTrue(name._primary is names[0])
        self.assertEqual(name.surname, "")
        self.assertEqual(name.given, "John")
        self.assertTrue(name.maiden is None)

        self.assertEqual(name.order(model.ORDER_SURNAME_GIVEN), ("2", "1John"))
        self.assertEqual(name.order(model.ORDER_GIVEN_SURNAME), ("1John", "2"))
        self.assertEqual(name.order(model.ORDER_MAIDEN_GIVEN), ("2", "1John"))
        self.assertEqual(name.order(model.ORDER_GIVEN_MAIDEN), ("1John", "2"))

        self.assertEqual(name.format(model.FMT_DEFAULT), ("John"))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST), ("John"))
        self.assertEqual(name.format(model.FMT_SURNAME_FIRST), ("John"))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_COMMA), ("John"))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_MAIDEN), ("John"))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_MAIDEN_ONLY), ("John"))

        name_type = model.make_record(2, None, "TYPE", "maiden", [], 0, dialect).freeze()
        names = [model.make_record(1, None, "NAME", "/Sawyer/", [name_type], 0, dialect).freeze(),
                 model.make_record(1, None, "NAME", "Jane /Smith/ A.", [], 0, dialect).freeze()]
        name = model.Name(names, dialect)

        self.assertTrue(name._primary is names[1])
        self.assertEqual(name.surname, "Smith")
        self.assertEqual(name.given, "Jane A.")
        self.assertEqual(name.maiden, "Sawyer")

        self.assertEqual(name.order(model.ORDER_SURNAME_GIVEN), ("1Smith", "1Jane A."))
        self.assertEqual(name.order(model.ORDER_GIVEN_SURNAME), ("1Jane A.", "1Smith"))
        self.assertEqual(name.order(model.ORDER_MAIDEN_GIVEN), ("1Sawyer", "1Jane A."))
        self.assertEqual(name.order(model.ORDER_GIVEN_MAIDEN), ("1Jane A.", "1Sawyer"))

        self.assertEqual(name.format(model.FMT_DEFAULT), ("Jane Smith A."))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST), ("Jane A. Smith"))
        self.assertEqual(name.format(model.FMT_SURNAME_FIRST), ("Smith Jane A."))
        self.assertEqual(name.format(model.FMT_SURNAME_FIRST | model.FMT_COMMA), ("Smith, Jane A."))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_COMMA), ("Jane A. Smith"))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_MAIDEN), ("Jane A. Smith (Sawyer)"))
        self.assertEqual(name.format(model.FMT_SURNAME_FIRST | model.FMT_COMMA | model.FMT_MAIDEN), ("Smith (Sawyer), Jane A."))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_MAIDEN_ONLY), ("Jane A. Sawyer"))

    def test_021_name_altree(self):
        """Test Name class with ALTREE dialect."""

        dialect = model.DIALECT_ALTREE
        names = [model.make_record(1, None, "NAME", "Jane /Smith (Sawyer)/ A.", [], 0, dialect).freeze()]
        name = model.Name(names, dialect)

        self.assertTrue(name._primary is names[0])
        self.assertEqual(name.surname, "Smith")
        self.assertEqual(name.given, "Jane A.")
        self.assertEqual(name.maiden, "Sawyer")

        self.assertEqual(name.order(model.ORDER_SURNAME_GIVEN), ("1Smith", "1Jane A."))
        self.assertEqual(name.order(model.ORDER_GIVEN_SURNAME), ("1Jane A.", "1Smith"))
        self.assertEqual(name.order(model.ORDER_MAIDEN_GIVEN), ("1Sawyer", "1Jane A."))
        self.assertEqual(name.order(model.ORDER_GIVEN_MAIDEN), ("1Jane A.", "1Sawyer"))

        self.assertEqual(name.format(model.FMT_DEFAULT), ("Jane Smith A."))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST), ("Jane A. Smith"))
        self.assertEqual(name.format(model.FMT_SURNAME_FIRST), ("Smith Jane A."))
        self.assertEqual(name.format(model.FMT_SURNAME_FIRST | model.FMT_COMMA), ("Smith, Jane A."))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_COMMA), ("Jane A. Smith"))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_MAIDEN), ("Jane A. Smith (Sawyer)"))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_MAIDEN_ONLY), ("Jane A. Sawyer"))

        names = [model.make_record(1, None, "NAME", "Jane /?/ A.", [], 0, dialect).freeze()]
        name = model.Name(names, dialect)

        self.assertTrue(name._primary is names[0])
        self.assertEqual(name.surname, "")
        self.assertEqual(name.given, "Jane A.")
        self.assertTrue(name.maiden is None)

        self.assertEqual(name.order(model.ORDER_SURNAME_GIVEN), ("2", "1Jane A."))
        self.assertEqual(name.order(model.ORDER_GIVEN_SURNAME), ("1Jane A.", "2"))
        self.assertEqual(name.order(model.ORDER_MAIDEN_GIVEN), ("2", "1Jane A."))
        self.assertEqual(name.order(model.ORDER_GIVEN_MAIDEN), ("1Jane A.", "2"))

        self.assertEqual(name.format(model.FMT_DEFAULT), ("Jane A."))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST), ("Jane A."))
        self.assertEqual(name.format(model.FMT_SURNAME_FIRST), ("Jane A."))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_COMMA), ("Jane A."))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_MAIDEN), ("Jane A."))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_MAIDEN_ONLY), ("Jane A."))

    def test_022_name_myher(self):
        """Test Name class with MYHERITAGE dialect."""

        dialect = model.DIALECT_MYHERITAGE
        married = model.make_record(2, None, "_MARNM", "Smith", [], 0, dialect).freeze()
        names = [model.make_record(1, None, "NAME", "Jane /Sawyer/ A.", [married], 0, dialect).freeze()]
        name = model.Name(names, dialect)

        self.assertTrue(name._primary is names[0])
        self.assertEqual(name.surname, "Smith")
        self.assertEqual(name.given, "Jane A.")
        self.assertEqual(name.maiden, "Sawyer")

        self.assertEqual(name.order(model.ORDER_SURNAME_GIVEN), ("1Smith", "1Jane A."))
        self.assertEqual(name.order(model.ORDER_GIVEN_SURNAME), ("1Jane A.", "1Smith"))
        self.assertEqual(name.order(model.ORDER_MAIDEN_GIVEN), ("1Sawyer", "1Jane A."))
        self.assertEqual(name.order(model.ORDER_GIVEN_MAIDEN), ("1Jane A.", "1Sawyer"))

        self.assertEqual(name.format(model.FMT_DEFAULT), ("Jane Smith A."))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST), ("Jane A. Smith"))
        self.assertEqual(name.format(model.FMT_SURNAME_FIRST), ("Smith Jane A."))
        self.assertEqual(name.format(model.FMT_SURNAME_FIRST | model.FMT_COMMA), ("Smith, Jane A."))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_COMMA), ("Jane A. Smith"))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_MAIDEN), ("Jane A. Smith (Sawyer)"))
        self.assertEqual(name.format(model.FMT_GIVEN_FIRST | model.FMT_MAIDEN_ONLY), ("Jane A. Sawyer"))

    def test_030_date(self):
        """Test Date class."""

        dialect = model.DIALECT_MYHERITAGE
        date = model.make_record(1, None, "DATE", "1970", [], 0, dialect).freeze()
        self.assertIsInstance(date, model.Date)
        self.assertIsInstance(date.value, DateValue)

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
        self.assertTrue(type(rec) is model.NameRec)
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
