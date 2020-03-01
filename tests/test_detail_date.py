#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ged4py.detail.date` module."""

import unittest

from ged4py.detail.date import CalendarDate, DateValue


class TestDetailName(unittest.TestCase):
    """Tests for `ged4py.detail.io` module."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_001_cal_date(self):
        """Test detail.date.CalendarDate class."""

        date = CalendarDate("2017", "OCT", 9, "GREGORIAN")
        self.assertEqual(date.year, "2017")
        self.assertEqual(date.month, "OCT")
        self.assertEqual(date.day, 9)
        self.assertEqual(date.calendar, "GREGORIAN")

        date = CalendarDate("2017B.C.", "OCT", None, None)
        self.assertEqual(date.year, "2017B.C.")
        self.assertEqual(date.month, "OCT")
        self.assertTrue(date.day is None)
        self.assertEqual(date.calendar, "GREGORIAN")

        date = CalendarDate("5000", calendar="HEBREW")
        self.assertEqual(date.year, "5000")
        self.assertTrue(date.month is None)
        self.assertTrue(date.day is None)
        self.assertEqual(date.calendar, "HEBREW")

        date = CalendarDate()
        self.assertTrue(date.year is None)
        self.assertTrue(date.month is None)
        self.assertTrue(date.day is None)
        self.assertEqual(date.calendar, "GREGORIAN")

    def test_002_cal_date_as_tuple(self):
        """Test detail.date.CalendarDate class."""

        date = CalendarDate("2017", "OCT", 9, "GREGORIAN")
        self.assertEqual(date.as_tuple, (2017, 10, 9))

        date = CalendarDate("2017B.C.", "VENT", None, "FRENCH R")
        self.assertEqual(date.as_tuple, (2017, 6, 99))

        date = CalendarDate("2017B.C.", "TSH", 22, "HEBREW")
        self.assertEqual(date.as_tuple, (2017, 1, 22))

        date = CalendarDate("5000")
        self.assertEqual(date.as_tuple, (5000, 99, 99))

        date = CalendarDate()
        self.assertEqual(date.as_tuple, (9999, 99, 99))

    def test_003_cal_date_cmp(self):
        """Test detail.date.CalendarDate class."""

        self.assertTrue(CalendarDate("2016", "JAN", 1) < CalendarDate("2017", "JAN", 1))
        self.assertTrue(CalendarDate("2017", "JAN", 1) < CalendarDate("2017", "FEB", 1))
        self.assertTrue(CalendarDate("2017", "JAN", 1) < CalendarDate("2017", "JAN", 2))

        self.assertTrue(CalendarDate("2017", "JAN", 1) <= CalendarDate("2017", "JAN", 2))
        self.assertTrue(CalendarDate("2017", "JAN", 2) > CalendarDate("2017", "JAN", 1))
        self.assertTrue(CalendarDate("2017", "JAN", 2) >= CalendarDate("2017", "JAN", 1))
        self.assertTrue(CalendarDate("2017", "JAN", 1) == CalendarDate("2017", "JAN", 1))
        self.assertTrue(CalendarDate("2017", "JAN", 1) != CalendarDate("2017", "JAN", 2))

        # missing day compares as "past" the last day of month, but before next month
        self.assertTrue(CalendarDate("2017", "JAN") > CalendarDate("2017", "JAN", 31))
        self.assertTrue(CalendarDate("2017", "JAN") < CalendarDate("2017", "FEB", 1))
        # missing month compares as "past" the last day of year, but before next year
        self.assertTrue(CalendarDate("2017") > CalendarDate("2017", "DEC", 31))
        self.assertTrue(CalendarDate("2017") < CalendarDate("2018", "JAN", 1))

    def test_004_cal_date_fmt(self):
        """Test detail.date.CalendarDate class."""
        date = CalendarDate("2017", "OCT", 9, "GREGORIAN")
        self.assertEqual(date.fmt(), "2017 OCT 9")

        date = CalendarDate("2017B.C.", "OCT", None, None)
        self.assertEqual(date.fmt(), "2017B.C. OCT")

        date = CalendarDate("5000", calendar="HEBREW")
        self.assertEqual(date.fmt(), "5000")

    def test_010_date(self):
        """Test detail.date.DateValue class."""

        date = DateValue()
        self.assertEqual(date.template, "")
        self.assertEqual(date.kw, {})

        date = DateValue("$date", {})
        self.assertEqual(date.template, "$date")
        self.assertEqual(date.kw, {})

        date = DateValue("FROM $date1 TO $date2",
                         {"date1": CalendarDate("2017"),
                          "date2": CalendarDate("2020")})
        self.assertEqual(date.template, "FROM $date1 TO $date2")
        self.assertEqual(date.kw, {"date1": CalendarDate("2017"),
                                   "date2": CalendarDate("2020")})
        self.assertEqual(date.fmt(), "FROM 2017 TO 2020")

        # "phrase" keyword corresponds to string
        date = DateValue("FROM $date1 TO ($phrase)",
                         {"date1": CalendarDate("2017"),
                          "phrase": "some day"})
        self.assertEqual(date.fmt(), "FROM 2017 TO (some day)")

    def test_011_date_fmt(self):
        """Test detail.date.DateValue class."""

        date = DateValue("date", {})
        self.assertEqual(date.fmt(), "date")

        date = DateValue("FROM $date1 TO $date2",
                         {"date1": CalendarDate("2017"),
                          "date2": CalendarDate("2020")})
        self.assertEqual(date.fmt(), "FROM 2017 TO 2020")

        date = DateValue("BET $date1 AND $date2",
                         {"date1": CalendarDate("2017", "JAN", 1),
                          "date2": CalendarDate("2020", "FLOR", 20)})
        self.assertEqual(date.fmt(), "BET 2017 JAN 1 AND 2020 FLOR 20")

    def test_012_date_parse_period(self):
        """Test detail.date.DateValue class."""

        date = DateValue.parse("FROM 1967")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "FROM $date")
        self.assertEqual(date.kw, {"date": CalendarDate("1967")})
        self.assertEqual(date.fmt(), "FROM 1967")

        date = DateValue.parse("TO 1 JAN 2017")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "TO $date")
        self.assertEqual(date.kw, {"date": CalendarDate("2017", "JAN", 1)})
        self.assertEqual(date.fmt(), "TO 2017 JAN 1")

        date = DateValue.parse("FROM 1920 TO 2000")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "FROM $date1 TO $date2")
        self.assertEqual(date.kw, {"date1": CalendarDate("1920"),
                                   "date2": CalendarDate("2000")})
        self.assertEqual(date.fmt(), "FROM 1920 TO 2000")

        date = DateValue.parse("from mar 1920 to 1 apr 2000")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "FROM $date1 TO $date2")
        self.assertEqual(date.kw, {"date1": CalendarDate("1920", "MAR"),
                                   "date2": CalendarDate("2000", "APR", 1)})

    def test_013_date_parse_range(self):
        """Test detail.date.DateValue class."""

        date = DateValue.parse("BEF 1967A.D.")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "BEFORE $date")
        self.assertEqual(date.kw, {"date": CalendarDate("1967A.D.")})
        self.assertEqual(date.fmt(), "BEFORE 1967A.D.")

        date = DateValue.parse("AFT 1 JAN 2017")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "AFTER $date")
        self.assertEqual(date.kw, {"date": CalendarDate("2017", "JAN", 1)})
        self.assertEqual(date.fmt(), "AFTER 2017 JAN 1")

        date = DateValue.parse("BET @#DJULIAN@ 1600 AND 2000")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "BETWEEN $date1 AND $date2")
        self.assertEqual(date.kw, {"date1": CalendarDate("1600"),
                                   "date2": CalendarDate("2000")})
        self.assertEqual(date.fmt(), "BETWEEN 1600 AND 2000")

        date = DateValue.parse("bet mar 1920 and apr 2000")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "BETWEEN $date1 AND $date2")
        self.assertEqual(date.kw, {"date1": CalendarDate("1920", "MAR"),
                                   "date2": CalendarDate("2000", "APR")})
        self.assertEqual(date.fmt(), "BETWEEN 1920 MAR AND 2000 APR")

    def test_014_date_parse_approx(self):
        """Test detail.date.DateValue class."""

        dates = {"500B.C.": CalendarDate("500B.C."),
                 "@#DGREGORIAN@ JAN 2017": CalendarDate("2017", "JAN"),
                 "31 JAN 2017": CalendarDate("2017", "JAN", 31)}

        approx = {"ABT": "ABOUT", "CAL": "CALCULATED", "EST": "ESTIMATED"}

        for appr, tmpl in approx.items():
            for datestr, value in dates.items():

                date = DateValue.parse(appr + " " + datestr)
                self.assertTrue(date is not None)
                self.assertEqual(date.template, tmpl + " $date")
                self.assertEqual(date.kw, {"date": value})

    def test_015_date_parse_phrase(self):
        """Test detail.date.DateValue class."""

        date = DateValue.parse("(some phrase)")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "($phrase)")
        self.assertEqual(date.kw, {"phrase": "some phrase"})

        date = DateValue.parse("INT 1967A.D. (some phrase)")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "INTERPRETED $date ($phrase)")
        self.assertEqual(date.kw, {"date": CalendarDate("1967A.D."),
                                   "phrase": "some phrase"})
        self.assertEqual(date.fmt(), "INTERPRETED 1967A.D. (some phrase)")

        date = DateValue.parse("INT @#DGREGORIAN@ 1 JAN 2017 (some phrase)")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "INTERPRETED $date ($phrase)")
        self.assertEqual(date.kw, {"date": CalendarDate("2017", "JAN", 1),
                                   "phrase": "some phrase"})
        self.assertEqual(date.fmt(), "INTERPRETED 2017 JAN 1 (some phrase)")

    def test_016_date_parse_simple(self):
        """Test detail.date.DateValue class."""

        date = DateValue.parse("1967A.D.")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "$date")
        self.assertEqual(date.kw, {"date": CalendarDate("1967A.D.")})
        self.assertEqual(date.fmt(), "1967A.D.")

        date = DateValue.parse("@#DGREGORIAN@ 1 JAN 2017")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "$date")
        self.assertEqual(date.kw, {"date": CalendarDate("2017", "JAN", 1)})
        self.assertEqual(date.fmt(), "2017 JAN 1")

    def test_017_date_cmp(self):
        """Test detail.date.Date class."""

        dv = DateValue.parse("2016")
        self.assertIsInstance(dv._cmp_date, CalendarDate)
        self.assertEqual(dv._cmp_date, CalendarDate("2016"))

        dv = DateValue.parse("31 DEC 2000")
        self.assertIsInstance(dv._cmp_date, CalendarDate)
        self.assertEqual(dv._cmp_date, CalendarDate("2000", "DEC", 31))

        dv = DateValue.parse("BET 31 DEC 2000 AND 1 JAN 2001")
        self.assertIsInstance(dv._cmp_date, CalendarDate)
        self.assertEqual(dv._cmp_date, CalendarDate("2000", "DEC", 31))

        # earliest date
        dv = DateValue.parse("BET 31 DEC 2000 AND 1 JAN 2000")
        self.assertIsInstance(dv._cmp_date, CalendarDate)
        self.assertEqual(dv._cmp_date, CalendarDate("2000", "JAN", 1))

        self.assertTrue(DateValue.parse("2016") < DateValue.parse("2017"))
        self.assertTrue(DateValue.parse("2 JAN 2016") > DateValue.parse("1 JAN 2016"))
        self.assertTrue(DateValue.parse("BET 1900 AND 2000") < DateValue.parse("FROM 1920 TO 1999"))

        # Less specific date compares later than more specific
        self.assertTrue(DateValue.parse("2000") > DateValue.parse("31 DEC 2000"))
        self.assertTrue(DateValue.parse("DEC 2000") > DateValue.parse("31 DEC 2000"))

        # phrase is always later than any regular date
        self.assertTrue(DateValue.parse("(Could be 1996 or 1998)") > DateValue.parse("2000"))

        # "empty" date is always later than any regular date
        self.assertTrue(DateValue() > DateValue.parse("2000"))

    def test_018_date_parse_empty(self):
        """Test detail.date.DateValue class."""

        for value in (None, ""):
            date = DateValue.parse(value)
            self.assertTrue(date is not None)
            self.assertEqual(date.template, "")
            self.assertEqual(date.kw, {})
            self.assertEqual(date.fmt(), "")
