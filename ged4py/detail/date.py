"""Internal module for parsing dates in gedcom format.
"""

from __future__ import print_function, absolute_import, division

__all__ = ["CalendarDate"]

import re


class CalendarDate(object):
    """Representation of calendar date, corresponding to <DATE> element.

    This includes optional calendar kind (calendar escape) which can be
    one of @#DHEBREW@ | @#DROMAN@ | @#DFRENCH R@ | @#DGREGORIAN@ |
    @#DJULIAN@ | @#DUNKNOWN@ (@#DGREGORIAN@) is default. Date consists
    of year, month, and day; day and moth are optional (eitehr day or
    day+month), year must be present. Day is a number, month is month name
    in given calendar. Year is a number optionally followed by "B.C." or
    "/NN".

    Dates can be ordered but ordering only works for the dates from the
    same calendar, dates from different calendars will be ordered randomly.

    In general date parsing tries to make best effort to guess all possible
    formats, but if it fails it does not raise exceptions, instead it uses
    some defaults values for items that cannot be understood.

    :param str year: String representing year in a calendar. Expected to
        start with few digits and followed by some suffix.
    :param str month: Name of the month. Optional, but if day is given then
        month cannot be None.
    :param int day: Day in a month, optional.
    :param str calendar: one of "GREGORIAN", "JULIAN", "HERBEW", "ROMAN",
        "FRENCH R", "UNKNOWN", default is "GREGORIAN"
    """

    DIGITS = re.compile(r"\d+")
    MONTHS_GREG = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    MONTHS_HERB = ['TSH', 'CSH', 'KSL', 'TVT', 'SHV', 'ADR', 'ADS', 'NSN', 'IYR', 'SVN', 'TMZ', 'AAV', 'ELL']
    MONTHS_FREN = ['VEND', 'BRUM', 'FRIM', 'NIVO', 'PLUV', 'VENT', 'GERM', 'FLOR', 'PRAI', 'MESS', 'THER', 'FRUC', 'COMP']
    MONTHS = {"GREGORIAN": MONTHS_GREG,
              "JULIAN": MONTHS_GREG,
              "HERBEW": MONTHS_HERB,
              "FRENCH R": MONTHS_FREN}

    def __init__(self, year, month=None, day=None, calendar=None):
        self.year = year
        self.month = month
        self.day = day
        self.calendar = calendar or "GREGORIAN"

        self._tuple = None

    @property
    def as_tuple(self):
        """Date as three-tuple of numbers"""
        if self._tuple is None:
            # extract leading digits from year
            m = self.DIGITS.match(self.year)
            year = int(m.group(0)) if m else 9999

            # month is a string from a calendar (None works ok here too
            months = self.MONTHS.get(self.calendar, [])
            try:
                month = months.index(self.month)
            except ValueError:
                month = 99

            day = self.day if self.day is not None else 99

            # should we include calendar name in tuple too?
            self._tuple = year, month, day

        return self._tuple

    def __lt__(self, other):
        return self.as_tuple < other.as_tuple

    def __le__(self, other):
        return self.as_tuple <= other.as_tuple

    def __eq__(self, other):
        return self.as_tuple == other.as_tuple

    def __ne__(self, other):
        return self.as_tuple != other.as_tuple

    def __gt__(self, other):
        return self.as_tuple > other.as_tuple

    def __ge__(self, other):
        return self.as_tuple >= other.as_tuple
