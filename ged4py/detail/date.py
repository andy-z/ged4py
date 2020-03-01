"""Internal module for parsing dates in gedcom format.
"""

from __future__ import print_function, absolute_import, division

__all__ = ["CalendarDate", "DateValue"]

import re
import string


MONTHS_GREG = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG',
               'SEP', 'OCT', 'NOV', 'DEC']
MONTHS_HEBR = ['TSH', 'CSH', 'KSL', 'TVT', 'SHV', 'ADR', 'ADS', 'NSN',
               'IYR', 'SVN', 'TMZ', 'AAV', 'ELL']
MONTHS_FREN = ['VEND', 'BRUM', 'FRIM', 'NIVO', 'PLUV', 'VENT', 'GERM',
               'FLOR', 'PRAI', 'MESS', 'THER', 'FRUC', 'COMP']

# DATE_VALUE := [
#     <DATE> |
#     <DATE_PERIOD> |
#     <DATE_RANGE>|
#     <DATE_APPROXIMATED> |
#     INT <DATE> (<DATE_PHRASE>) |
#     (<DATE_PHRASE>)
#     ]

# DATE := [<DATE_CALENDAR_ESCAPE> | <NULL>] <DATE_CALENDAR>
# <DATE_CALENDAR> := [<YEAR> | <MONTH> <YEAR> | <DAY> <MONTH> <YEAR>]
# <YEAR can be specified as "1000B.C." or "1699/00"
# <MONTH> is all characters.
# This does not use named groups, it may appear few times in other expressions
# Groups: 1: calendar; 2: day; 3: month; 4: year
DATE = r"""
    (?:@\#D(\w+)@\s+)?          # @#DCALENDAR@, optional
    (?:
        (?:(\d+)\s+)?           # day (int), optional
        ([A-Z]{3,4})\s+         # month, name 3-4 chars,
    )?
    (\d+\S*)                    # year, required, number with optional suffix
    """
DATE_RE = re.compile("^" + DATE + "$", re.X | re.I)

# DATE_PERIOD:= [ FROM <DATE> | TO <DATE> | FROM <DATE> TO <DATE> ]
DATE_PERIOD_FROM = r"^FROM\s+(?P<date>" + DATE + ")$"
DATE_PERIOD_TO = r"^TO\s+(?P<date>" + DATE + ")$"
DATE_PERIOD = r"^FROM\s+(?P<date1>" + DATE + r")\s+TO\s+(?P<date2>" + \
              DATE + ")$"

# DATE_RANGE:= [ BEF <DATE> | AFT <DATE> | BET <DATE> AND <DATE> ]
DATE_RANGE_BEFORE = r"^BEF\s+(?P<date>" + DATE + ")$"
DATE_RANGE_AFTER = r"^AFT\s+(?P<date>" + DATE + ")$"
DATE_RANGE = r"^BET\s+(?P<date1>" + DATE + r")\s+AND\s+(?P<date2>" + \
             DATE + ")$"

# DATE_APPROXIMATED := [ ABT <DATE> | CAL <DATE> | EST <DATE> ]
DATE_APPROX_ABOUT = r"^ABT\s+(?P<date>" + DATE + ")$"
DATE_APPROX_CALC = r"^CAL\s+(?P<date>" + DATE + ")$"
DATE_APPROX_EST = r"^EST\s+(?P<date>" + DATE + ")$"

# INT <DATE> (<DATE_PHRASE>)
DATE_INTERP = r"^INT\s+(?P<date>" + DATE + r")\s+\((?P<phrase>.*)\)$"
DATE_PHRASE = r"^\((?P<phrase>.*)\)$"

# INT <DATE> (<DATE_PHRASE>)
DATE_SIMPLE = r"^(?P<date>" + DATE + ")$"

DATES = ((re.compile(DATE_PERIOD, re.X | re.I), "FROM $date1 TO $date2"),
         (re.compile(DATE_PERIOD_FROM, re.X | re.I), "FROM $date"),
         (re.compile(DATE_PERIOD_TO, re.X | re.I), "TO $date"),
         (re.compile(DATE_RANGE, re.X | re.I), "BETWEEN $date1 AND $date2"),
         (re.compile(DATE_RANGE_BEFORE, re.X | re.I), "BEFORE $date"),
         (re.compile(DATE_RANGE_AFTER, re.X | re.I), "AFTER $date"),
         (re.compile(DATE_APPROX_ABOUT, re.X | re.I), "ABOUT $date"),
         (re.compile(DATE_APPROX_CALC, re.X | re.I), "CALCULATED $date"),
         (re.compile(DATE_APPROX_EST, re.X | re.I), "ESTIMATED $date"),
         (re.compile(DATE_INTERP, re.X | re.I), "INTERPRETED $date ($phrase)"),
         (re.compile(DATE_PHRASE, re.X | re.I), "($phrase)"),
         (re.compile(DATE_SIMPLE, re.X | re.I), "$date"),
         )


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
    :param str calendar: one of "GREGORIAN", "JULIAN", "HEBREW", "ROMAN",
        "FRENCH R", "UNKNOWN", default is "GREGORIAN"
    """

    DIGITS = re.compile(r"\d+")
    MONTHS = {"GREGORIAN": MONTHS_GREG,
              "JULIAN": MONTHS_GREG,
              "HEBREW": MONTHS_HEBR,
              "FRENCH R": MONTHS_FREN}

    def __init__(self, year=None, month=None, day=None, calendar=None):
        self.year = year
        self.month = None if month is None else month.upper()
        self.day = day
        self.calendar = calendar or "GREGORIAN"

        # determine month number
        months = self.MONTHS.get(self.calendar, [])
        try:
            self.month_num = months.index(self.month) + 1
        except ValueError:
            self.month_num = None

        self._tuple = None

    @classmethod
    def parse(cls, datestr):
        """Parse <DATE> string and make :py:class:`CalendarDate` from it.

        :param str datestr: String with GEDCOM date.
        """
        m = DATE_RE.match(datestr)
        if m is not None:
            day = None if m.group(2) is None else int(m.group(2))
            return cls(m.group(4), m.group(3), day, m.group(1))

    @property
    def as_tuple(self):
        """Date as three-tuple of numbers"""
        if self._tuple is None:
            # extract leading digits from year
            year = 9999
            if self.year:
                m = self.DIGITS.match(self.year)
                if m:
                    year = int(m.group(0))
            month = self.month_num or 99
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

    def fmt(self):
        """Make printable representation out of this instance.
        """
        val = str(self.year)
        if self.month is not None:
            val += ' ' + str(self.month)
            if self.day is not None:
                val += ' ' + str(self.day)
        return val

    def __str__(self):
        return "{}(year={}, month={}, day={}, calendar={})".format(
            self.__class__.__name__, self.year, self.month,
            self.day, self.calendar)

    def __repr__(self):
        return str(self)


class DateValue(object):
    """Representation of the <DATE_VALUE>, can be exact date, range,
    period, etc.

    If `kw` is empty (default) then resulting DateValue is guaranteed to be
    in the future w.r.t. any regular dates.

    :param str tmpl: Template string acceptable by `string.Template`.
    :param dict kw: Dictionary with the keys being keywords in template
        string and values are instance of :py:class:`CalendarDate` or
        strings.
    """

    def __init__(self, tmpl="", kw={}):
        self.template = tmpl
        self.kw = kw

    @classmethod
    def parse(cls, datestr):
        """Parse string <DATE_VALUE> string and make :py:class:`DateValue`
        instance out of it.

        :param str datestr: String with GEDCOM date, range, period, etc.
        """
        # some apps generate DATE recods without any value, which is
        # non-standard, return empty DateValue for those
        if not datestr:
            return cls()
        for regex, tmpl in DATES:
            m = regex.match(datestr)
            if m is not None:
                groups = {}
                for key, val in m.groupdict().items():
                    if key != 'phrase':
                        val = CalendarDate.parse(val)
                    groups[key] = val
                return cls(tmpl, groups)
        # if cannot parse string assume it is a phrase
        return cls("($phrase)", dict(phrase=datestr))

    @property
    def _cmp_date(self):
        """Returns Calendar date used for comparison.

        Use the earliest date out of all CalendarDates in this instance,
        or some date in the future if there are no CalendarDates (e.g.
        when Date is a phrase).
        """
        dates = sorted(val for val in self.kw.values()
                       if isinstance(val, CalendarDate))
        if dates:
            return dates[0]
        # return date very far in the future
        return CalendarDate()

    def __lt__(self, other):
        return self._cmp_date < other._cmp_date

    def __le__(self, other):
        return self._cmp_date <= other._cmp_date

    def __eq__(self, other):
        return self._cmp_date == other._cmp_date

    def __ne__(self, other):
        return self._cmp_date != other._cmp_date

    def __gt__(self, other):
        return self._cmp_date > other._cmp_date

    def __ge__(self, other):
        return self._cmp_date >= other._cmp_date

    def fmt(self):
        """Make printable representation out of this instance.
        """
        tmpl = string.Template(self.template)
        kw = {}
        for key, val in self.kw.items():
            if key == 'phrase':
                kw[key] = val
            else:
                kw[key] = val.fmt()
        return tmpl.substitute(kw)

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.fmt())

    def __repr__(self):
        return str(self)
