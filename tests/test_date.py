#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ged4py.detail.date` module."""

import unittest

from ged4py.date import CalendarDate, FrenchDate, GregorianDate, HebrewDate, JulianDate, DateValue


class TestDetailDate(unittest.TestCase):
    """Tests for `ged4py.detail.date` module."""

    def test_001_cal_date(self):
        """Test detail.date.CalendarDate class."""

        date = GregorianDate(2017, "OCT", 9)
        self.assertEqual(date.year, 2017)
        self.assertIsNone(date.dual_year)
        self.assertFalse(date.bc)
        self.assertEqual(date.year_str, "2017")
        self.assertEqual(date.month, "OCT")
        self.assertEqual(date.month_num, 10)
        self.assertEqual(date.day, 9)
        self.assertEqual(date.calendar, "GREGORIAN")

        date = GregorianDate(2017, "OCT", bc=True)
        self.assertEqual(date.year, 2017)
        self.assertIsNone(date.dual_year)
        self.assertTrue(date.bc)
        self.assertEqual(date.year_str, "2017 B.C.")
        self.assertEqual(date.month, "OCT")
        self.assertEqual(date.month_num, 10)
        self.assertIsNone(date.day)
        self.assertEqual(date.calendar, "GREGORIAN")

        date = GregorianDate(1699, "FEB", dual_year=1700)
        self.assertEqual(date.year, 1699)
        self.assertEqual(date.dual_year, 1700)
        self.assertFalse(date.bc)
        self.assertEqual(date.year_str, "1699/00")
        self.assertEqual(date.month, "FEB")
        self.assertEqual(date.month_num, 2)
        self.assertIsNone(date.day)
        self.assertEqual(date.calendar, "GREGORIAN")

        date = HebrewDate(5000)
        self.assertEqual(date.year, 5000)
        self.assertFalse(date.bc)
        self.assertEqual(date.year_str, "5000")
        self.assertIsNone(date.month)
        self.assertIsNone(date.month_num)
        self.assertIsNone(date.day)
        self.assertEqual(date.calendar, "HEBREW")

        date = FrenchDate(1, "FRUC", 1)
        self.assertEqual(date.year, 1)
        self.assertFalse(date.bc)
        self.assertEqual(date.year_str, "1")
        self.assertEqual(date.month, "FRUC")
        self.assertEqual(date.month_num, 12)
        self.assertEqual(date.day, 1)
        self.assertEqual(date.calendar, "FRENCH R")

        date = JulianDate(5, "JAN", bc=True)
        self.assertEqual(date.year, 5)
        self.assertTrue(date.bc)
        self.assertEqual(date.year_str, "5 B.C.")
        self.assertEqual(date.month, "JAN")
        self.assertEqual(date.month_num, 1)
        self.assertIsNone(date.day)
        self.assertEqual(date.calendar, "JULIAN")

    def test_002_cal_date_key(self):
        """Test detail.date.CalendarDate class."""

        date = GregorianDate(2017, "OCT", 9)
        self.assertEqual(date.key(), (2458035.5, 0))

        date = GregorianDate(1699, "FEB", 1, dual_year=1700)
        self.assertEqual(date.key(), (2342003.5, 0))

        date = FrenchDate(2017, "VENT", bc=True)
        self.assertEqual(date.key(), (1638959.5, 1))

        date = HebrewDate(2017, "TSH", 22)
        self.assertEqual(date.key(), (1084542.5, 0))

        date = JulianDate(1000)
        self.assertEqual(date.key(), (2086672.5, 1))

    def test_003_cal_date_cmp(self):
        """Test detail.date.CalendarDate class."""

        self.assertTrue(GregorianDate(2016, "JAN", 1) < GregorianDate(2017, "JAN", 1))
        self.assertTrue(GregorianDate(2017, "JAN", 1) < GregorianDate(2017, "FEB", 1))
        self.assertTrue(GregorianDate(2017, "JAN", 1) < GregorianDate(2017, "JAN", 2))

        self.assertTrue(GregorianDate(2017, "JAN", 1) <= GregorianDate(2017, "JAN", 2))
        self.assertTrue(GregorianDate(2017, "JAN", 2) > GregorianDate(2017, "JAN", 1))
        self.assertTrue(GregorianDate(2017, "JAN", 2) >= GregorianDate(2017, "JAN", 1))
        self.assertTrue(GregorianDate(2017, "JAN", 1) == GregorianDate(2017, "JAN", 1))
        self.assertTrue(GregorianDate(2017, "JAN", 1) != GregorianDate(2017, "JAN", 2))

        # missing day compares as "past" the last day of month, but before next month
        self.assertTrue(GregorianDate(2017, "JAN") > GregorianDate(2017, "JAN", 31))
        self.assertTrue(GregorianDate(2017, "JAN") < GregorianDate(2017, "FEB", 1))
        # missing month compares as "past" the last day of year, but before next year
        self.assertTrue(GregorianDate(2017) > GregorianDate(2017, "DEC", 31))
        self.assertTrue(GregorianDate(2017) < GregorianDate(2018, "JAN", 1))

        # dual date
        self.assertTrue(GregorianDate(1700, "JAN", 1) == GregorianDate(1699, "JAN", 1, dual_year=1700))

        # compare Gregorian and Julian dates
        self.assertTrue(GregorianDate(1582, "OCT", 15) == JulianDate(1582, "OCT", 5))
        self.assertTrue(GregorianDate(1582, "OCT", 16) > JulianDate(1582, "OCT", 5))
        self.assertTrue(JulianDate(1582, "OCT", 6) > GregorianDate(1582, "OCT", 15))
        self.assertTrue(GregorianDate(2000, "JAN", 14) == JulianDate(2000, "JAN", 1))

        # compare Gregorian and French dates
        self.assertTrue(GregorianDate(1792, "SEP", 22) == FrenchDate(1, "VEND", 1))
        self.assertTrue(GregorianDate(1792, "SEP", 23) > FrenchDate(1, "VEND", 1))
        self.assertTrue(FrenchDate(1, "VEND", 2) > GregorianDate(1792, "SEP", 22))
        self.assertTrue(GregorianDate(2020, "SEP", 21) == FrenchDate(228, "COMP", 5))

        # compare Gregorian and Hebrew dates
        self.assertTrue(GregorianDate(2020, "JAN", 1) == HebrewDate(5780, "SVN", 4))

    def test_004_cal_date_fmt(self):
        """Test detail.date.CalendarDate class."""
        date = GregorianDate(2017, "OCT", 9)
        self.assertEqual(date.fmt(), "9 OCT 2017")

        date = GregorianDate(2017, "OCT", bc=True)
        self.assertEqual(date.fmt(), "OCT 2017 B.C.")

        date = GregorianDate(1699, "JAN", 1, dual_year=1700)
        self.assertEqual(date.fmt(), "1 JAN 1699/00")

        date = HebrewDate(5000)
        self.assertEqual(date.fmt(), "5000")

        date = FrenchDate(1, "VEND", 1)
        self.assertEqual(date.fmt(), "1 VEND 1")

        date = JulianDate(1582, "OCT", 5)
        self.assertEqual(date.fmt(), "5 OCT 1582")

    def test_005_cal_date_parse(self):
        """Test detail.date.CalendarDate.parse method."""

        date = CalendarDate.parse("31 MAY 2020")
        self.assertIsInstance(date, GregorianDate)
        self.assertEqual(date.year, 2020)
        self.assertIsNone(date.dual_year)
        self.assertFalse(date.bc)
        self.assertEqual(date.month, "MAY")
        self.assertEqual(date.month_num, 5)
        self.assertEqual(date.day, 31)
        self.assertEqual(date.original, "31 MAY 2020")
        self.assertEqual(date.calendar, "GREGORIAN")

        date = CalendarDate.parse("@#DGREGORIAN@ 10 MAR 1698/99")
        self.assertIsInstance(date, GregorianDate)
        self.assertEqual(date.year, 1698)
        self.assertEqual(date.dual_year, 1699)
        self.assertFalse(date.bc)
        self.assertEqual(date.month, "MAR")
        self.assertEqual(date.month_num, 3)
        self.assertEqual(date.day, 10)
        self.assertEqual(date.original, "@#DGREGORIAN@ 10 MAR 1698/99")
        self.assertEqual(date.calendar, "GREGORIAN")

        date = CalendarDate.parse("10 MAR 1699/00")
        self.assertIsInstance(date, GregorianDate)
        self.assertEqual(date.year, 1699)
        self.assertEqual(date.dual_year, 1700)
        self.assertEqual(date.original, "10 MAR 1699/00")
        self.assertEqual(date.calendar, "GREGORIAN")

        date = CalendarDate.parse("@#DJULIAN@ 100 B.C.")
        self.assertIsInstance(date, JulianDate)
        self.assertEqual(date.year, 100)
        self.assertTrue(date.bc)
        self.assertIsNone(date.month)
        self.assertIsNone(date.month_num)
        self.assertIsNone(date.day)
        self.assertEqual(date.original, "@#DJULIAN@ 100 B.C.")
        self.assertEqual(date.calendar, "JULIAN")

        date = CalendarDate.parse("@#DFRENCH@ 15 GERM 0001")
        self.assertIsInstance(date, FrenchDate)
        self.assertEqual(date.year, 1)
        self.assertFalse(date.bc)
        self.assertEqual(date.month, "GERM")
        self.assertEqual(date.month_num, 7)
        self.assertEqual(date.day, 15)
        self.assertEqual(date.original, "@#DFRENCH@ 15 GERM 0001")
        self.assertEqual(date.calendar, "FRENCH R")

        date = CalendarDate.parse("@#DHEBREW@ 7 NSN 5000")
        self.assertIsInstance(date, HebrewDate)
        self.assertEqual(date.year, 5000)
        self.assertFalse(date.bc)
        self.assertEqual(date.month, "NSN")
        self.assertEqual(date.month_num, 8)
        self.assertEqual(date.day, 7)
        self.assertEqual(date.original, "@#DHEBREW@ 7 NSN 5000")
        self.assertEqual(date.calendar, "HEBREW")

        # cannot handle ROMAN
        with self.assertRaises(ValueError):
            date = CalendarDate.parse("@#DROMAN@ 2020")

        # cannot handle UNKNOWN
        with self.assertRaises(ValueError):
            date = CalendarDate.parse("@#DUNKNOWN@ 2020")

        # dual year only works for GREGORIAN
        with self.assertRaises(ValueError):
            date = CalendarDate.parse("@#DJULIAN@ 2020/21")

        # cannot parse nonsense
        with self.assertRaises(ValueError):
            date = CalendarDate.parse("start of time")

    def test_010_date(self):
        """Test detail.date.DateValue class."""

        date = DateValue()
        self.assertEqual(date.template, "")
        self.assertEqual(date.kw, {})

        date = DateValue("$date", {})
        self.assertEqual(date.template, "$date")
        self.assertEqual(date.kw, {})

        date = DateValue("FROM $date1 TO $date2",
                         {"date1": GregorianDate(2017),
                          "date2": GregorianDate(2020)})
        self.assertEqual(date.template, "FROM $date1 TO $date2")
        self.assertEqual(date.kw, {"date1": GregorianDate(2017),
                                   "date2": GregorianDate(2020)})
        self.assertEqual(date.fmt(), "FROM 2017 TO 2020")

        # "phrase" keyword corresponds to string
        date = DateValue("FROM $date1 TO ($phrase)",
                         {"date1": GregorianDate(2017),
                          "phrase": "some day"})
        self.assertEqual(date.fmt(), "FROM 2017 TO (some day)")

    def test_011_date_fmt(self):
        """Test detail.date.DateValue class."""

        date = DateValue("date", {})
        self.assertEqual(date.fmt(), "date")

        date = DateValue("FROM $date1 TO $date2",
                         {"date1": GregorianDate(2017),
                          "date2": GregorianDate(2020)})
        self.assertEqual(date.fmt(), "FROM 2017 TO 2020")

        date = DateValue("BET $date1 AND $date2",
                         {"date1": GregorianDate(2017, "JAN", 1),
                          "date2": FrenchDate(2020, "FLOR", 20)})
        self.assertEqual(date.fmt(), "BET 1 JAN 2017 AND 20 FLOR 2020")

    def test_012_date_parse_period(self):
        """Test detail.date.DateValue class."""

        date = DateValue.parse("FROM 1967")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "FROM $date")
        self.assertEqual(date.kw, {"date": GregorianDate(1967)})
        self.assertEqual(date.fmt(), "FROM 1967")

        date = DateValue.parse("TO 1 JAN 2017")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "TO $date")
        self.assertEqual(date.kw, {"date": GregorianDate(2017, "JAN", 1)})
        self.assertEqual(date.fmt(), "TO 1 JAN 2017")

        date = DateValue.parse("FROM 1920 TO 2000")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "FROM $date1 TO $date2")
        self.assertEqual(date.kw, {"date1": GregorianDate(1920),
                                   "date2": GregorianDate(2000)})
        self.assertEqual(date.fmt(), "FROM 1920 TO 2000")

        date = DateValue.parse("from mar 1920 to 1 apr 2000")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "FROM $date1 TO $date2")
        self.assertEqual(date.kw, {"date1": GregorianDate(1920, "MAR"),
                                   "date2": GregorianDate(2000, "APR", 1)})

    def test_013_date_parse_range(self):
        """Test detail.date.DateValue class."""

        date = DateValue.parse("BEF 1967B.C.")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "BEFORE $date")
        self.assertEqual(date.kw, {"date": GregorianDate(1967, bc=True)})
        self.assertEqual(date.fmt(), "BEFORE 1967 B.C.")

        date = DateValue.parse("AFT 1 JAN 2017")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "AFTER $date")
        self.assertEqual(date.kw, {"date": GregorianDate(2017, "JAN", 1)})
        self.assertEqual(date.fmt(), "AFTER 1 JAN 2017")

        date = DateValue.parse("BET @#DJULIAN@ 1600 AND 2000")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "BETWEEN $date1 AND $date2")
        self.assertEqual(date.kw, {"date1": JulianDate(1600),
                                   "date2": GregorianDate(2000)})
        self.assertEqual(date.fmt(), "BETWEEN 1600 AND 2000")

        date = DateValue.parse("bet mar 1920 and apr 2000")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "BETWEEN $date1 AND $date2")
        self.assertEqual(date.kw, {"date1": GregorianDate(1920, "MAR"),
                                   "date2": GregorianDate(2000, "APR")})
        self.assertEqual(date.fmt(), "BETWEEN MAR 1920 AND APR 2000")

    def test_014_date_parse_approx(self):
        """Test detail.date.DateValue class."""

        dates = {"500B.C.": GregorianDate(500, bc=True),
                 "@#DGREGORIAN@ JAN 2017": GregorianDate(2017, "JAN"),
                 "31 JAN 2017": GregorianDate(2017, "JAN", 31)}

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

        date = DateValue.parse("INT 1967 B.C. (some phrase)")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "INTERPRETED $date ($phrase)")
        self.assertEqual(date.kw, {"date": GregorianDate(1967, bc=True),
                                   "phrase": "some phrase"})
        self.assertEqual(date.fmt(), "INTERPRETED 1967 B.C. (some phrase)")

        date = DateValue.parse("INT @#DGREGORIAN@ 1 JAN 2017 (some phrase)")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "INTERPRETED $date ($phrase)")
        self.assertEqual(date.kw, {"date": GregorianDate(2017, "JAN", 1),
                                   "phrase": "some phrase"})
        self.assertEqual(date.fmt(), "INTERPRETED 1 JAN 2017 (some phrase)")

    def test_016_date_parse_simple(self):
        """Test detail.date.DateValue class."""

        date = DateValue.parse("1967 B.C.")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "$date")
        self.assertEqual(date.kw, {"date": GregorianDate(1967, bc=True)})
        self.assertEqual(date.fmt(), "1967 B.C.")

        date = DateValue.parse("@#DGREGORIAN@ 1 JAN 2017")
        self.assertTrue(date is not None)
        self.assertEqual(date.template, "$date")
        self.assertEqual(date.kw, {"date": GregorianDate(2017, "JAN", 1)})
        self.assertEqual(date.fmt(), "1 JAN 2017")

    def test_017_date_cmp(self):
        """Test detail.date.Date class."""

        dv = DateValue.parse("2016")
        self.assertIsInstance(dv._cmp_date, CalendarDate)
        self.assertEqual(dv._cmp_date, GregorianDate(2016))

        dv = DateValue.parse("31 DEC 2000")
        self.assertIsInstance(dv._cmp_date, CalendarDate)
        self.assertEqual(dv._cmp_date, GregorianDate(2000, "DEC", 31))

        dv = DateValue.parse("BET 31 DEC 2000 AND 1 JAN 2001")
        self.assertIsInstance(dv._cmp_date, CalendarDate)
        self.assertEqual(dv._cmp_date, GregorianDate(2000, "DEC", 31))

        # earliest date
        dv = DateValue.parse("BET 31 DEC 2000 AND 1 JAN 2000")
        self.assertIsInstance(dv._cmp_date, CalendarDate)
        self.assertEqual(dv._cmp_date, GregorianDate(2000, "JAN", 1))

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
