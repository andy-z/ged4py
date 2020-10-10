#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ged4py.date` module."""

import unittest

from ged4py.calendar import (
    CalendarType, CalendarDate, FrenchDate, GregorianDate, HebrewDate, JulianDate,
    CalendarDateVisitor
)
from ged4py.date import (
    DateValue, DateValueAbout, DateValueAfter, DateValueBefore, DateValueCalculated,
    DateValueEstimated, DateValueFrom, DateValueInterpreted, DateValuePeriod,
    DateValuePhrase, DateValueRange, DateValueSimple, DateValueTo, DateValueTypes,
    DateValueVisitor
)


class TestDateVisitor(CalendarDateVisitor, DateValueVisitor):

    def visitGregorian(self, date):
        if not isinstance(date, GregorianDate):
            raise TypeError(str(type(date)))
        return ("gregorian", date)

    def visitJulian(self, date):
        if not isinstance(date, JulianDate):
            raise TypeError(str(type(date)))
        return ("julian", date)

    def visitHebrew(self, date):
        if not isinstance(date, HebrewDate):
            raise TypeError(str(type(date)))
        return ("hebrew", date)

    def visitFrench(self, date):
        if not isinstance(date, FrenchDate):
            raise TypeError(str(type(date)))
        return ("french", date)

    def visitSimple(self, date):
        if not isinstance(date, DateValueSimple):
            raise TypeError(str(type(date)))
        return ("simple", date.date)

    def visitPeriod(self, date):
        if not isinstance(date, DateValuePeriod):
            raise TypeError(str(type(date)))
        return ("period", date.date1, date.date2)

    def visitFrom(self, date):
        if not isinstance(date, DateValueFrom):
            raise TypeError(str(type(date)))
        return ("from", date.date)

    def visitTo(self, date):
        if not isinstance(date, DateValueTo):
            raise TypeError(str(type(date)))
        return ("to", date.date)

    def visitRange(self, date):
        if not isinstance(date, DateValueRange):
            raise TypeError(str(type(date)))
        return ("range", date.date1, date.date2)

    def visitBefore(self, date):
        if not isinstance(date, DateValueBefore):
            raise TypeError(str(type(date)))
        return ("before", date.date)

    def visitAfter(self, date):
        if not isinstance(date, DateValueAfter):
            raise TypeError(str(type(date)))
        return ("after", date.date)

    def visitAbout(self, date):
        if not isinstance(date, DateValueAbout):
            raise TypeError(str(type(date)))
        return ("about", date.date)

    def visitCalculated(self, date):
        if not isinstance(date, DateValueCalculated):
            raise TypeError(str(type(date)))
        return ("calculated", date.date)

    def visitEstimated(self, date):
        if not isinstance(date, DateValueEstimated):
            raise TypeError(str(type(date)))
        return ("estimated", date.date)

    def visitInterpreted(self, date):
        if not isinstance(date, DateValueInterpreted):
            raise TypeError(str(type(date)))
        return ("interpreted", date.date, date.phrase)

    def visitPhrase(self, date):
        if not isinstance(date, DateValuePhrase):
            raise TypeError(str(type(date)))
        return ("phrase", date.phrase)


class TestDetailDate(unittest.TestCase):
    """Tests for `ged4py.date` module."""

    def test_001_cal_date(self):
        """Test date.CalendarDate class."""

        date = GregorianDate(2017, "OCT", 9)
        self.assertEqual(date.year, 2017)
        self.assertIsNone(date.dual_year)
        self.assertFalse(date.bc)
        self.assertEqual(date.year_str, "2017")
        self.assertEqual(date.month, "OCT")
        self.assertEqual(date.month_num, 10)
        self.assertEqual(date.day, 9)
        self.assertEqual(date.calendar, CalendarType.GREGORIAN)

        date = GregorianDate(2017, "OCT", bc=True)
        self.assertEqual(date.year, 2017)
        self.assertIsNone(date.dual_year)
        self.assertTrue(date.bc)
        self.assertEqual(date.year_str, "2017 B.C.")
        self.assertEqual(date.month, "OCT")
        self.assertEqual(date.month_num, 10)
        self.assertIsNone(date.day)
        self.assertEqual(date.calendar, CalendarType.GREGORIAN)

        date = GregorianDate(1699, "FEB", dual_year=1700)
        self.assertEqual(date.year, 1699)
        self.assertEqual(date.dual_year, 1700)
        self.assertFalse(date.bc)
        self.assertEqual(date.year_str, "1699/00")
        self.assertEqual(date.month, "FEB")
        self.assertEqual(date.month_num, 2)
        self.assertIsNone(date.day)
        self.assertEqual(date.calendar, CalendarType.GREGORIAN)

        date = HebrewDate(5000)
        self.assertEqual(date.year, 5000)
        self.assertFalse(date.bc)
        self.assertEqual(date.year_str, "5000")
        self.assertIsNone(date.month)
        self.assertIsNone(date.month_num)
        self.assertIsNone(date.day)
        self.assertEqual(date.calendar, CalendarType.HEBREW)

        date = FrenchDate(1, "FRUC", 1)
        self.assertEqual(date.year, 1)
        self.assertFalse(date.bc)
        self.assertEqual(date.year_str, "1")
        self.assertEqual(date.month, "FRUC")
        self.assertEqual(date.month_num, 12)
        self.assertEqual(date.day, 1)
        self.assertEqual(date.calendar, CalendarType.FRENCH_R)

        date = JulianDate(5, "JAN", bc=True)
        self.assertEqual(date.year, 5)
        self.assertTrue(date.bc)
        self.assertEqual(date.year_str, "5 B.C.")
        self.assertEqual(date.month, "JAN")
        self.assertEqual(date.month_num, 1)
        self.assertIsNone(date.day)
        self.assertEqual(date.calendar, CalendarType.JULIAN)

    def test_002_cal_date_key(self):
        """Test date.CalendarDate class."""

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
        """Test date.CalendarDate class."""

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

    def test_004_cal_date_str(self):
        """Test date.CalendarDate class."""
        date = GregorianDate(2017, "OCT", 9)
        self.assertEqual(str(date), "9 OCT 2017")

        date = GregorianDate(2017, "OCT", bc=True)
        self.assertEqual(str(date), "OCT 2017 B.C.")

        date = GregorianDate(1699, "JAN", 1, dual_year=1700)
        self.assertEqual(str(date), "1 JAN 1699/00")

        date = HebrewDate(5000)
        self.assertEqual(str(date), "@#DHEBREW@ 5000")

        date = FrenchDate(1, "VEND", 1)
        self.assertEqual(str(date), "@#DFRENCH R@ 1 VEND 1")

        date = JulianDate(1582, "OCT", 5)
        self.assertEqual(str(date), "@#DJULIAN@ 5 OCT 1582")

    def test_005_cal_date_parse(self):
        """Test date.CalendarDate.parse method."""

        date = CalendarDate.parse("31 MAY 2020")
        self.assertIsInstance(date, GregorianDate)
        self.assertEqual(date.year, 2020)
        self.assertIsNone(date.dual_year)
        self.assertFalse(date.bc)
        self.assertEqual(date.month, "MAY")
        self.assertEqual(date.month_num, 5)
        self.assertEqual(date.day, 31)
        self.assertEqual(date.original, "31 MAY 2020")
        self.assertEqual(date.calendar, CalendarType.GREGORIAN)

        date = CalendarDate.parse("@#DGREGORIAN@ 10 MAR 1698/99")
        self.assertIsInstance(date, GregorianDate)
        self.assertEqual(date.year, 1698)
        self.assertEqual(date.dual_year, 1699)
        self.assertFalse(date.bc)
        self.assertEqual(date.month, "MAR")
        self.assertEqual(date.month_num, 3)
        self.assertEqual(date.day, 10)
        self.assertEqual(date.original, "@#DGREGORIAN@ 10 MAR 1698/99")
        self.assertEqual(date.calendar, CalendarType.GREGORIAN)

        date = CalendarDate.parse("10 MAR 1699/00")
        self.assertIsInstance(date, GregorianDate)
        self.assertEqual(date.year, 1699)
        self.assertEqual(date.dual_year, 1700)
        self.assertEqual(date.original, "10 MAR 1699/00")
        self.assertEqual(date.calendar, CalendarType.GREGORIAN)

        date = CalendarDate.parse("@#DJULIAN@ 100 B.C.")
        self.assertIsInstance(date, JulianDate)
        self.assertEqual(date.year, 100)
        self.assertTrue(date.bc)
        self.assertIsNone(date.month)
        self.assertIsNone(date.month_num)
        self.assertIsNone(date.day)
        self.assertEqual(date.original, "@#DJULIAN@ 100 B.C.")
        self.assertEqual(date.calendar, CalendarType.JULIAN)

        date = CalendarDate.parse("@#DFRENCH R@ 15 GERM 0001")
        self.assertIsInstance(date, FrenchDate)
        self.assertEqual(date.year, 1)
        self.assertFalse(date.bc)
        self.assertEqual(date.month, "GERM")
        self.assertEqual(date.month_num, 7)
        self.assertEqual(date.day, 15)
        self.assertEqual(date.original, "@#DFRENCH R@ 15 GERM 0001")
        self.assertEqual(date.calendar, CalendarType.FRENCH_R)

        date = CalendarDate.parse("@#DHEBREW@ 7 NSN 5000")
        self.assertIsInstance(date, HebrewDate)
        self.assertEqual(date.year, 5000)
        self.assertFalse(date.bc)
        self.assertEqual(date.month, "NSN")
        self.assertEqual(date.month_num, 8)
        self.assertEqual(date.day, 7)
        self.assertEqual(date.original, "@#DHEBREW@ 7 NSN 5000")
        self.assertEqual(date.calendar, CalendarType.HEBREW)

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

    def test_006_cal_date_visitor(self):
        """Test date.CalendarDate.accept method."""

        visitor = TestDateVisitor()

        date = GregorianDate(2017, "OCT", 9)
        value = date.accept(visitor)
        self.assertEqual(value, ("gregorian", date))

        date = HebrewDate(5000)
        value = date.accept(visitor)
        self.assertEqual(value, ("hebrew", date))

        date = FrenchDate(1, "VEND", 1)
        value = date.accept(visitor)
        self.assertEqual(value, ("french", date))

        date = JulianDate(1582, "OCT", 5)
        value = date.accept(visitor)
        self.assertEqual(value, ("julian", date))

    def test_007_cal_date_hash(self):
        """Test date.CalendarDate hash."""

        self.assertEqual(hash(GregorianDate(2017, "OCT", 9)),
                         hash(GregorianDate(2017, "OCT", 9)))
        self.assertEqual(hash(GregorianDate(2017, "OCT", 9, bc=True)),
                         hash(GregorianDate(2017, "OCT", 9, bc=True)))
        self.assertEqual(hash(FrenchDate(1, "VEND", 1)),
                         hash(FrenchDate(1, "VEND", 1)))
        self.assertEqual(hash(FrenchDate(1)),
                         hash(FrenchDate(1)))

    def test_010_date_no_date(self):
        """Test date.DateValue class."""

        date = DateValue.parse("not a date")
        self.assertIsInstance(date, DateValuePhrase)
        self.assertEqual(date.kind, DateValueTypes.PHRASE)
        self.assertEqual(date.phrase, "not a date")
        self.assertEqual(str(date), "(not a date)")

    def test_012_date_parse_period(self):
        """Test date.DateValue class."""

        date = DateValue.parse("FROM 1967")
        self.assertIsInstance(date, DateValueFrom)
        self.assertEqual(date.kind, DateValueTypes.FROM)
        self.assertEqual(date.date, GregorianDate(1967))
        self.assertEqual(str(date), "FROM 1967")

        date = DateValue.parse("TO 1 JAN 2017")
        self.assertIsInstance(date, DateValueTo)
        self.assertEqual(date.kind, DateValueTypes.TO)
        self.assertEqual(date.date, GregorianDate(2017, "JAN", 1))
        self.assertEqual(str(date), "TO 1 JAN 2017")

        date = DateValue.parse("FROM 1920 TO 2000")
        self.assertIsInstance(date, DateValuePeriod)
        self.assertEqual(date.kind, DateValueTypes.PERIOD)
        self.assertEqual(date.date1, GregorianDate(1920))
        self.assertEqual(date.date2, GregorianDate(2000))
        self.assertEqual(str(date), "FROM 1920 TO 2000")

        date = DateValue.parse("from mar 1920 to 1 apr 2000")
        self.assertIsInstance(date, DateValuePeriod)
        self.assertEqual(date.kind, DateValueTypes.PERIOD)
        self.assertEqual(date.date1, GregorianDate(1920, "MAR"))
        self.assertEqual(date.date2, GregorianDate(2000, "APR", 1))
        self.assertEqual(str(date), "FROM MAR 1920 TO 1 APR 2000")

    def test_013_date_parse_range(self):
        """Test date.DateValue class."""

        date = DateValue.parse("BEF 1967B.C.")
        self.assertIsInstance(date, DateValueBefore)
        self.assertEqual(date.kind, DateValueTypes.BEFORE)
        self.assertEqual(date.date, GregorianDate(1967, bc=True))
        self.assertEqual(str(date), "BEFORE 1967 B.C.")

        date = DateValue.parse("AFT 1 JAN 2017")
        self.assertIsInstance(date, DateValueAfter)
        self.assertEqual(date.kind, DateValueTypes.AFTER)
        self.assertEqual(date.date, GregorianDate(2017, "JAN", 1))
        self.assertEqual(str(date), "AFTER 1 JAN 2017")

        date = DateValue.parse("BET @#DJULIAN@ 1600 AND 2000")
        self.assertIsInstance(date, DateValueRange)
        self.assertEqual(date.kind, DateValueTypes.RANGE)
        self.assertEqual(date.date1, JulianDate(1600))
        self.assertEqual(date.date2, GregorianDate(2000))
        self.assertEqual(str(date), "BETWEEN @#DJULIAN@ 1600 AND 2000")

        date = DateValue.parse("bet mar 1920 and apr 2000")
        self.assertIsInstance(date, DateValueRange)
        self.assertEqual(date.kind, DateValueTypes.RANGE)
        self.assertEqual(date.date1, GregorianDate(1920, "MAR"))
        self.assertEqual(date.date2, GregorianDate(2000, "APR"))
        self.assertEqual(str(date), "BETWEEN MAR 1920 AND APR 2000")

    def test_014_date_parse_approx(self):
        """Test date.DateValue class."""

        dates = {"500 B.C.": GregorianDate(500, bc=True),
                 "JAN 2017": GregorianDate(2017, "JAN"),
                 "31 JAN 2017": GregorianDate(2017, "JAN", 31)}

        approx = [
            ("ABT", "ABOUT", DateValueAbout, DateValueTypes.ABOUT),
            ("CAL", "CALCULATED", DateValueCalculated, DateValueTypes.CALCULATED),
            ("EST", "ESTIMATED", DateValueEstimated, DateValueTypes.ESTIMATED)
        ]

        for appr, fmt, klass, typeEnum in approx:
            for datestr, value in dates.items():
                date = DateValue.parse(appr + " " + datestr)
                self.assertIsInstance(date, klass)
                self.assertEqual(date.kind, typeEnum)
                self.assertEqual(str(date), fmt + " " + datestr)
                self.assertEqual(date.date, value)

    def test_015_date_parse_phrase(self):
        """Test date.DateValue class."""

        date = DateValue.parse("(some phrase)")
        self.assertIsInstance(date, DateValuePhrase)
        self.assertEqual(date.kind, DateValueTypes.PHRASE)
        self.assertEqual(date.phrase, "some phrase")

        date = DateValue.parse("INT 1967 B.C. (some phrase)")
        self.assertIsInstance(date, DateValueInterpreted)
        self.assertEqual(date.kind, DateValueTypes.INTERPRETED)
        self.assertEqual(date.date, GregorianDate(1967, bc=True))
        self.assertEqual(date.phrase, "some phrase")
        self.assertEqual(str(date), "INTERPRETED 1967 B.C. (some phrase)")

        date = DateValue.parse("INT @#DGREGORIAN@ 1 JAN 2017 (some phrase)")
        self.assertIsInstance(date, DateValueInterpreted)
        self.assertEqual(date.kind, DateValueTypes.INTERPRETED)
        self.assertEqual(date.date, GregorianDate(2017, "JAN", 1))
        self.assertEqual(date.phrase, "some phrase")
        self.assertEqual(str(date), "INTERPRETED 1 JAN 2017 (some phrase)")

    def test_016_date_parse_simple(self):
        """Test date.DateValue class."""

        date = DateValue.parse("1967 B.C.")
        self.assertIsInstance(date, DateValueSimple)
        self.assertEqual(date.kind, DateValueTypes.SIMPLE)
        self.assertEqual(date.date, GregorianDate(1967, bc=True))
        self.assertEqual(str(date), "1967 B.C.")

        date = DateValue.parse("@#DGREGORIAN@ 1 JAN 2017")
        self.assertIsInstance(date, DateValueSimple)
        self.assertEqual(date.kind, DateValueTypes.SIMPLE)
        self.assertEqual(date.date, GregorianDate(2017, "JAN", 1))
        self.assertEqual(str(date), "1 JAN 2017")

    def test_017_date_cmp(self):
        """Test date.Date class."""

        dv = DateValue.parse("2016")
        self.assertIsInstance(dv.key(), tuple)
        self.assertEqual(dv.key(), (GregorianDate(2016), GregorianDate(2016)))

        dv = DateValue.parse("31 DEC 2000")
        self.assertIsInstance(dv.key(), tuple)
        self.assertEqual(dv.key(), (GregorianDate(2000, "DEC", 31), GregorianDate(2000, "DEC", 31)))

        dv = DateValue.parse("BET 31 DEC 2000 AND 1 JAN 2001")
        self.assertIsInstance(dv.key(), tuple)
        self.assertEqual(dv.key(), (GregorianDate(2000, "DEC", 31), GregorianDate(2001, "JAN", 1)))

        # order of dates is messed up
        dv = DateValue.parse("BET 31 DEC 2000 AND 1 JAN 2000")
        self.assertIsInstance(dv.key(), tuple)
        self.assertEqual(dv.key(), (GregorianDate(2000, "DEC", 31), GregorianDate(2000, "JAN", 1)))

        self.assertTrue(DateValue.parse("2016") < DateValue.parse("2017"))
        self.assertTrue(DateValue.parse("2 JAN 2016") > DateValue.parse("1 JAN 2016"))
        self.assertTrue(DateValue.parse("BET 1900 AND 2000") < DateValue.parse("FROM 1920 TO 1999"))

        # comparing simple date with range
        self.assertTrue(DateValue.parse("1 JAN 2000") > DateValue.parse("BET 1 JAN 1999 AND 1 JAN 2000"))
        self.assertNotEqual(DateValue.parse("1 JAN 2000"), DateValue.parse("BET 1 JAN 2000 AND 1 JAN 2001"))
        self.assertTrue(DateValue.parse("1 JAN 2000") < DateValue.parse("BET 1 JAN 2000 AND 1 JAN 2001"))
        self.assertTrue(DateValue.parse("1 JAN 2000") > DateValue.parse("BEF 1 JAN 2000"))
        self.assertTrue(DateValue.parse("1 JAN 2000") > DateValue.parse("TO 1 JAN 2000"))
        self.assertTrue(DateValue.parse("1 JAN 2000") < DateValue.parse("AFT 1 JAN 2000"))
        self.assertTrue(DateValue.parse("1 JAN 2000") < DateValue.parse("FROM 1 JAN 2000"))

        # comparing ranges
        self.assertEqual(DateValue.parse("FROM 1 JAN 2000 TO 1 JAN 2001"),
                         DateValue.parse("BET 1 JAN 2000 AND 1 JAN 2001"))
        self.assertTrue(DateValue.parse("FROM 1 JAN 1999 TO 1 JAN 2001") <
                        DateValue.parse("BET 1 JAN 2000 AND 1 JAN 2001"))
        self.assertTrue(DateValue.parse("FROM 1 JAN 2000 TO 1 JAN 2002") >
                        DateValue.parse("BET 1 JAN 2000 AND 1 JAN 2001"))

        # Less specific date compares later than more specific
        self.assertTrue(DateValue.parse("2000") > DateValue.parse("31 DEC 2000"))
        self.assertTrue(DateValue.parse("DEC 2000") > DateValue.parse("31 DEC 2000"))

        # phrase is always later than any regular date
        self.assertTrue(DateValue.parse("(Could be 1996 or 1998)") > DateValue.parse("2000"))

        # "empty" date is always later than any regular date
        self.assertTrue(DateValue.parse("") > DateValue.parse("2000"))

    def test_018_date_parse_empty(self):
        """Test date.DateValue class."""

        for value in (None, ""):
            date = DateValue.parse(value)
            self.assertIsInstance(date, DateValuePhrase)
            self.assertEqual(date.kind, DateValueTypes.PHRASE)
            self.assertIsNone(date.phrase)
            self.assertEqual(str(date), "")

    def test_019_date_value_visitor(self):
        """Test date.DateValue class."""

        visitor = TestDateVisitor()

        date1 = GregorianDate(2017, "JAN", 1)
        date2 = GregorianDate(2017, "DEC", 31)

        value = DateValueSimple(date1).accept(visitor)
        self.assertEqual(value, ("simple", date1))

        value = DateValueFrom(date1).accept(visitor)
        self.assertEqual(value, ("from", date1))

        value = DateValueTo(date1).accept(visitor)
        self.assertEqual(value, ("to", date1))

        value = DateValuePeriod(date1, date2).accept(visitor)
        self.assertEqual(value, ("period", date1, date2))

        value = DateValueBefore(date1).accept(visitor)
        self.assertEqual(value, ("before", date1))

        value = DateValueAfter(date1).accept(visitor)
        self.assertEqual(value, ("after", date1))

        value = DateValueRange(date1, date2).accept(visitor)
        self.assertEqual(value, ("range", date1, date2))

        value = DateValueAbout(date1).accept(visitor)
        self.assertEqual(value, ("about", date1))

        value = DateValueCalculated(date1).accept(visitor)
        self.assertEqual(value, ("calculated", date1))

        value = DateValueEstimated(date1).accept(visitor)
        self.assertEqual(value, ("estimated", date1))

        value = DateValueInterpreted(date1, "phrase").accept(visitor)
        self.assertEqual(value, ("interpreted", date1, "phrase"))

        value = DateValuePhrase("phrase").accept(visitor)
        self.assertEqual(value, ("phrase", "phrase"))

    def test_020_date_hash(self):
        """Test date.Date hash"""

        dv1 = DateValue.parse("2016")
        dv2 = DateValue.parse("2016")
        self.assertEqual(hash(dv1), hash(dv2))

        dv1 = DateValue.parse("31 DEC 2000")
        dv2 = DateValue.parse("31 DEC 2000")
        self.assertEqual(hash(dv1), hash(dv2))

        dv1 = DateValue.parse("BET 31 DEC 2000 AND 1 JAN 2001")
        dv2 = DateValue.parse("BET 31 DEC 2000 AND 1 JAN 2001")
        self.assertEqual(hash(dv1), hash(dv2))
