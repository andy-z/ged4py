#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ged4py.model` module."""

import unittest

from ged4py import model
from ged4py.date import DateValue, DateValueSimple


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
        rec.dialect = model.Dialect.DEFAULT

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
        rec.dialect = model.Dialect.DEFAULT

        for subtag in ['SUBA', 'SUBB', 'SUBC']:
            for i in range(3):

                sub = model.Record()
                sub.level = 1
                sub.tag = subtag
                sub.value = i
                sub.sub_records = []
                sub.offset = 1100 + 100 * i
                sub.dialect = model.Dialect.DEFAULT

                subsub = model.Record()
                subsub.level = 2
                subsub.tag = "SUB"
                subsub.value = 'VALUE'
                subsub.sub_records = []
                subsub.dialect = model.Dialect.DEFAULT
                subsub.freeze()

                sub.sub_records.append(subsub)
                sub.freeze()

                rec.sub_records.append(sub)

        # direct sub-tags
        rec.freeze()
        for subtag in ['SUBA', 'SUBB', 'SUBC']:
            self.assertEqual(rec.sub_tag(subtag).tag, subtag)
            self.assertEqual(len(rec.sub_tags(subtag)), 3)

        # non-existing sub-tags
        self.assertTrue(rec.sub_tag("SUB") is None)
        self.assertEqual(rec.sub_tags("SUB"), [])
        self.assertTrue(rec.sub_tag_value("SUB") is None)

        # hierarchical sub-tags
        self.assertTrue(rec.sub_tag("SUBA/SUB") is not None)
        self.assertEqual(rec.sub_tag("SUBB/SUB").tag, "SUB")
        self.assertEqual(rec.sub_tag_value("SUBB/SUB"), "VALUE")

    def test_003_record_nohash(self):
        """Test that records are non-hashable"""

        rec = model.Record()
        with self.assertRaises(TypeError):
            d = {}
            d[rec] = ""
        with self.assertRaises(TypeError):
            hash(rec)

    def test_010_namerec_default(self):
        """Test NameRec class with default dialect."""

        rec = model.NameRec()
        rec.level = 1
        rec.tag = "NAME"
        rec.dialect = model.Dialect.DEFAULT

        rec.value = ""
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("", "", ""))

        rec.value = None
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
        rec.dialect = model.Dialect.ALTREE

        rec.value = ""
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("", "", ""))

        rec.value = None
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("", "", ""))

        rec.value = "First /Last Name/ Second "
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("First", "Last Name", "Second"))

        maiden = model.Record()
        maiden.level = 2
        maiden.tag = "SURN"
        maiden.value = "Maiden"
        rec.value = "First /Last (Maiden)/"
        rec.sub_records = [maiden]
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("First", "Last", "", "Maiden"))

    def test_012_namerec_myher(self):
        """Test NameRec class with MYHERITAGE dialect."""

        rec = model.NameRec()
        rec.level = 1
        rec.tag = "NAME"
        rec.dialect = model.Dialect.MYHERITAGE
        rec.sub_records = []

        rec.value = ""
        rec.freeze()
        self.assertIsInstance(rec.value, tuple)
        self.assertEqual(rec.value, ("", "", ""))

        rec.value = None
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

        dialect = model.Dialect.DEFAULT
        names = [model.make_record(1, None, "NAME", "John /Smith/", [], 0, dialect).freeze()]
        name = model.Name(names, dialect)

        self.assertTrue(name._primary is names[0])
        self.assertEqual(name.surname, "Smith")
        self.assertEqual(name.given, "John")
        self.assertTrue(name.maiden is None)

        self.assertEqual(name.order(model.NameOrder.SURNAME_GIVEN), ("1Smith", "1John"))
        self.assertEqual(name.order(model.NameOrder.GIVEN_SURNAME), ("1John", "1Smith"))
        self.assertEqual(name.order(model.NameOrder.MAIDEN_GIVEN), ("1Smith", "1John"))
        self.assertEqual(name.order(model.NameOrder.GIVEN_MAIDEN), ("1John", "1Smith"))

        self.assertEqual(name.format(), ("John Smith"))

        names = [model.make_record(1, None, "NAME", "John", [], 0, dialect).freeze()]
        name = model.Name(names, dialect)

        self.assertTrue(name._primary is names[0])
        self.assertEqual(name.surname, "")
        self.assertEqual(name.given, "John")
        self.assertTrue(name.maiden is None)

        self.assertEqual(name.order(model.NameOrder.SURNAME_GIVEN), ("2", "1John"))
        self.assertEqual(name.order(model.NameOrder.GIVEN_SURNAME), ("1John", "2"))
        self.assertEqual(name.order(model.NameOrder.MAIDEN_GIVEN), ("2", "1John"))
        self.assertEqual(name.order(model.NameOrder.GIVEN_MAIDEN), ("1John", "2"))

        self.assertEqual(name.format(), ("John"))

        name_type = model.make_record(2, None, "TYPE", "maiden", [], 0, dialect).freeze()
        names = [model.make_record(1, None, "NAME", "/Sawyer/", [name_type], 0, dialect).freeze(),
                 model.make_record(1, None, "NAME", "Jane /Smith/ A.", [], 0, dialect).freeze()]
        name = model.Name(names, dialect)

        self.assertTrue(name._primary is names[1])
        self.assertEqual(name.surname, "Smith")
        self.assertEqual(name.given, "Jane A.")
        self.assertEqual(name.maiden, "Sawyer")

        self.assertEqual(name.order(model.NameOrder.SURNAME_GIVEN), ("1Smith", "1Jane A."))
        self.assertEqual(name.order(model.NameOrder.GIVEN_SURNAME), ("1Jane A.", "1Smith"))
        self.assertEqual(name.order(model.NameOrder.MAIDEN_GIVEN), ("1Sawyer", "1Jane A."))
        self.assertEqual(name.order(model.NameOrder.GIVEN_MAIDEN), ("1Jane A.", "1Sawyer"))

        self.assertEqual(name.format(), ("Jane Smith A."))

    def test_021_name_altree(self):
        """Test Name class with ALTREE dialect."""

        dialect = model.Dialect.ALTREE
        surn = model.make_record(2, None, "SURN", "Sawyer", [], 0, dialect).freeze()
        names = [model.make_record(1, None, "NAME", "Jane /Smith (Sawyer)/ A.", [surn], 0, dialect).freeze()]
        name = model.Name(names, dialect)

        self.assertTrue(name._primary is names[0])
        self.assertEqual(name.surname, "Smith")
        self.assertEqual(name.given, "Jane A.")
        self.assertEqual(name.maiden, "Sawyer")

        self.assertEqual(name.order(model.NameOrder.SURNAME_GIVEN), ("1Smith", "1Jane A."))
        self.assertEqual(name.order(model.NameOrder.GIVEN_SURNAME), ("1Jane A.", "1Smith"))
        self.assertEqual(name.order(model.NameOrder.MAIDEN_GIVEN), ("1Sawyer", "1Jane A."))
        self.assertEqual(name.order(model.NameOrder.GIVEN_MAIDEN), ("1Jane A.", "1Sawyer"))

        self.assertEqual(name.format(), ("Jane Smith A."))

        names = [model.make_record(1, None, "NAME", "Jane /?/ A.", [], 0, dialect).freeze()]
        name = model.Name(names, dialect)

        self.assertTrue(name._primary is names[0])
        self.assertEqual(name.surname, "")
        self.assertEqual(name.given, "Jane A.")
        self.assertTrue(name.maiden is None)

        self.assertEqual(name.order(model.NameOrder.SURNAME_GIVEN), ("2", "1Jane A."))
        self.assertEqual(name.order(model.NameOrder.GIVEN_SURNAME), ("1Jane A.", "2"))
        self.assertEqual(name.order(model.NameOrder.MAIDEN_GIVEN), ("2", "1Jane A."))
        self.assertEqual(name.order(model.NameOrder.GIVEN_MAIDEN), ("1Jane A.", "2"))

        self.assertEqual(name.format(), ("Jane A."))

    def test_022_name_myher(self):
        """Test Name class with MYHERITAGE dialect."""

        dialect = model.Dialect.MYHERITAGE
        married = model.make_record(2, None, "_MARNM", "Smith", [], 0, dialect).freeze()
        names = [model.make_record(1, None, "NAME", "Jane /Sawyer/ A.", [married], 0, dialect).freeze()]
        name = model.Name(names, dialect)

        self.assertTrue(name._primary is names[0])
        self.assertEqual(name.surname, "Smith")
        self.assertEqual(name.given, "Jane A.")
        self.assertEqual(name.maiden, "Sawyer")

        self.assertEqual(name.order(model.NameOrder.SURNAME_GIVEN), ("1Smith", "1Jane A."))
        self.assertEqual(name.order(model.NameOrder.GIVEN_SURNAME), ("1Jane A.", "1Smith"))
        self.assertEqual(name.order(model.NameOrder.MAIDEN_GIVEN), ("1Sawyer", "1Jane A."))
        self.assertEqual(name.order(model.NameOrder.GIVEN_MAIDEN), ("1Jane A.", "1Sawyer"))

        self.assertEqual(name.format(), ("Jane Smith A."))

    def test_030_date(self):
        """Test Date class."""

        dialect = model.Dialect.MYHERITAGE
        date = model.make_record(1, None, "DATE", "1970", [], 0, dialect).freeze()
        self.assertIsInstance(date, model.Date)
        self.assertIsInstance(date.value, DateValue)

        # empty date tag makes Date with empty DateValue
        dialect = model.Dialect.DEFAULT
        date = model.make_record(1, None, "DATE", None, [], 0, dialect).freeze()
        self.assertIsInstance(date, model.Date)
        self.assertIsInstance(date.value, DateValue)

        date = model.make_record(1, None, "DATE", "", [], 0, dialect).freeze()
        self.assertIsInstance(date, model.Date)
        self.assertIsInstance(date.value, DateValue)

        # dates can have leading whitespaces
        date = model.make_record(1, None, "DATE", "   DEC 1999", [], 0, dialect).freeze()
        self.assertIsInstance(date, model.Date)
        self.assertIsInstance(date.value, DateValueSimple)

    def test_040_Pointer(self):
        """Test Pointer class."""

        class Parser(object):
            def __init__(self):
                self.xref0 = {b"@pointer0@": (0, "TAG0"),
                              b"@pointer1@": (1, "TAG1")}

            def read_record(self, offset):
                return str(offset)

        pointer = model.Pointer(Parser())
        pointer.value = b"@pointer0@"
        pointer.freeze()

        self.assertEqual(pointer.value, b"@pointer0@")
        self.assertEqual(pointer.ref, "0")

        dialect = model.Dialect.MYHERITAGE
        pointer = model.make_record(1, None, "FAMC", b"@pointer1@", [], 0, dialect, Parser()).freeze()
        self.assertIsInstance(pointer, model.Pointer)
        self.assertEqual(pointer.value, b"@pointer1@")
        self.assertEqual(pointer.ref, "1")

    def test_041_Pointer_sub(self):
        """Test Pointer class."""

        class Parser(object):
            def __init__(self):
                self.xref0 = {b"@pointer0@": (0, "TAG0"),
                              b"@pointer1@": (1, "TAG1")}

            def read_record(self, offset):
                return str(offset)

        dialect = model.Dialect.MYHERITAGE
        parser = Parser()
        husb = model.make_record(1, None, "HUSB", b"@pointer0@", [], 0, dialect, parser).freeze()
        wife = model.make_record(1, None, "WIFE", b"@pointer1@", [], 0, dialect, parser).freeze()
        fam = model.make_record(0, None, "FAM", "", [husb, wife], 0, dialect, parser).freeze()

        rec = fam.sub_tag("HUSB", follow=True)
        self.assertEqual(rec, "0")
        rec = fam.sub_tag("HUSB", follow=False)
        self.assertTrue(rec is not None)
        self.assertIsInstance(rec, model.Pointer)

        recs = fam.sub_tags("HUSB", "WIFE", follow=True)
        self.assertEqual(recs, ["0", "1"])
        recs = fam.sub_tags("HUSB", "WIFE", follow=False)
        self.assertEqual(len(recs), 2)
        self.assertIsInstance(recs[0], model.Pointer)
        self.assertIsInstance(recs[1], model.Pointer)

    def test_900_make_record(self):
        """Test make_record method()"""

        rec = model.make_record(0, "@xref@", "TAG", "value", [], 1000,
                                model.Dialect.DEFAULT)
        rec.freeze()
        self.assertTrue(type(rec) is model.Record)
        self.assertEqual(rec.level, 0)
        self.assertEqual(rec.xref_id, "@xref@")
        self.assertEqual(rec.tag, "TAG")
        self.assertEqual(rec.value, "value")
        self.assertEqual(rec.sub_records, [])
        self.assertEqual(rec.offset, 1000)
        self.assertEqual(rec.dialect, model.Dialect.DEFAULT)

        rec = model.make_record(1, None, "NAME", "Joe", [], 1000,
                                model.Dialect.ALTREE)
        rec.freeze()
        self.assertTrue(type(rec) is model.NameRec)
        self.assertEqual(rec.level, 1)
        self.assertTrue(rec.xref_id is None)
        self.assertEqual(rec.tag, "NAME")
        self.assertEqual(rec.value, ("Joe", "", ""))
        self.assertEqual(rec.sub_records, [])
        self.assertEqual(rec.offset, 1000)
        self.assertEqual(rec.dialect, model.Dialect.ALTREE)

        rec = model.make_record(0, "@I1@", "INDI", None, [], 1000,
                                model.Dialect.MYHERITAGE)
        rec.freeze()
        self.assertTrue(type(rec) is model.Individual)
        self.assertEqual(rec.level, 0)
        self.assertEqual(rec.xref_id, "@I1@")
        self.assertEqual(rec.tag, "INDI")
        self.assertTrue(rec.value is None)
        self.assertEqual(rec.sub_records, [])
        self.assertEqual(rec.offset, 1000)
        self.assertEqual(rec.dialect, model.Dialect.MYHERITAGE)
