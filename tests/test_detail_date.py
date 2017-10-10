#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ged4py.detail.date` module."""

import unittest

from ged4py.detail.date import CalendarDate


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

        date = CalendarDate("5000", calendar="HERBEW")
        self.assertEqual(date.year, "5000")
        self.assertTrue(date.month is None)
        self.assertTrue(date.day is None)
        self.assertEqual(date.calendar, "HERBEW")

    def test_001_cal_date_as_tuple(self):
        """Test detail.date.CalendarDate class."""

        date = CalendarDate("2017", "OCT", 9, "GREGORIAN")
        self.assertEqual(date.as_tuple, (2017, 9, 9))

        date = CalendarDate("2017B.C.", "VENT", None, "FRENCH R")
        self.assertEqual(date.as_tuple, (2017, 5, 99))

        date = CalendarDate("2017B.C.", "TSH", 22, "HERBEW")
        self.assertEqual(date.as_tuple, (2017, 0, 22))

        date = CalendarDate("5000")
        self.assertEqual(date.as_tuple, (5000, 99, 99))

    def test_001_cal_date_cmp(self):
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
