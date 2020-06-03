"""Internal module for parsing dates in gedcom format.
"""

from __future__ import print_function, absolute_import, division

__all__ = ["CalendarDate", "FrenchDate", "GregorianDate", "HebrewDate", "JulianDate",
           "DateValue"]

import re
import string

import convertdate.french_republican
import convertdate.gregorian
import convertdate.hebrew
import convertdate.julian

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
YEAR = r""
DATE = r"""
    (?:@\#D(\w+)@\s+)?          # @#DCALENDAR@, optional (group=1)
    (?:
        (?:(\d+)\s+)?           # day (int), optional (group=2)
        ([A-Z]{3,4})\s+         # month, name 3-4 chars (group=3)
    )?
    (?:
        (\d+)(?:/(\d+))?        # year, required, number with optional /NUMBER
                                # (group=4,5)
        (\s*?B\.C\.)?           # optional B.C. suffix (group=6)
    )
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
    """Interface for calendar date representation.

    This class defines attributes and methods that are common for all
    calendars defined in GEDCOM (though the meaning and representation can be
    different in different calendars). In GEDCOM date consists of year, month,
    and day; day and month are optional (either day or day+month), year must
    be present. Day is a number, month is month name in a given calendar.
    Year is a number optionally followed by "B.C." or "/`NUMBER`" (latter is
    defined for Gregorian calendar only).

    Implementation for different calendars are provided by subclasses which
    can implement additional attributes or methods. All subclasses need to
    implement `key` method to support ordering of the dates from different
    calendars.

    :param int year: Calendar year number. If ``bc`` parameter is ``True``
        then this number is before "epoch" of that calendar.
    :param str month: Name of the month. Optional, but if day is given then
        month cannot be None.
    :param int day: Day in a month, optional.
    :param bool bc: `True` if year has "B.C."
    :param str original: Original string representation of this date as it was
        specified in GEDCOM file, could be ``None``.
    """

    def __init__(self, year, month=None, day=None, bc=False, original=None):
        self.year = year
        """Calendar year number (`int`)"""
        self.month = None if month is None else month.upper()
        """Month name or ``None`` (`str`)"""
        self.day = day
        """Day number or ``None`` (`int`)"""
        self.bc = bc
        """Flag which is ``True`` if year has a "B.C" suffix (`bool`)."""
        self.original = original
        """Original string representation of this date as it was specified in
        GEDCOM file, could be ``None`` (`str`).
        """
        self.month_num = None
        """Integer month number (1-based) or ``None`` if month name is not
        given or unknown (`int`).
        """

        # determine month number
        months = self.months()
        try:
            self.month_num = months.index(self.month) + 1
        except ValueError:
            pass

    @classmethod
    def months(self):
        """Ordered list of month names (in GEDCOM format) defined in calendar.
        """
        raise NotImplementedError()

    def key(self):
        """Return ordering key for this instance.

        Returned key is a tuple with two numbers (jd, flag). ``jd`` is the
        Julian Day number as floating point, ``flag`` is an integer flag.
        If month or day is not known then last month or last day should be
        returned in its place (in corresponding calendar, and converted to
        JD) and ``flag`` should be set to 1. If date and month are known then
        flag should be set to 0.
        """
        raise NotImplementedError()

    @property
    def year_str(self):
        """Calendar year in string representation, this can include dual year
        and/or B.C. suffix (`str`)
        """
        year = str(self.year)
        if self.bc:
            year += " B.C."
        return year

    @property
    def calendar(self):
        """Calendar name usedfor this date (`str`)
        """
        raise NotImplementedError()

    @classmethod
    def parse(cls, datestr):
        """Parse <DATE> string and make :py:class:`CalendarDate` from it.

        :param str datestr: String with GEDCOM date.
        :returns: CalendarDate instance
        :raises: ValueError is raised if parsing fails.
        """

        def _dual_year(year_str, dual_year_str):
            """Guess dual year, returns actual year number.

            In GEDCOM dual year uses last two digits of the year number
            (though some implementations use four digits). This method
            tries to guess actual year number from the digits that were
            given, e.g. "1650/51" -> 1651; "1699/00" -> 1700.
            """
            if dual_year_str is None:
                return None
            if len(dual_year_str) >= len(year_str):
                return int(dual_year_str)
            dual_year_str = year_str[:len(year_str)-len(dual_year_str)] + dual_year_str
            year = int(year_str)
            dual_year = int(dual_year_str)
            while dual_year < year:
                dual_year += 100
            return dual_year

        m = DATE_RE.match(datestr)
        if m is None:
            raise ValueError("Failed to parse date: " + datestr)

        calendar = m.group(1) or "GREGORIAN"
        day = None if m.group(2) is None else int(m.group(2))
        month = m.group(3)
        year = int(m.group(4))
        dual_year = _dual_year(m.group(4), m.group(5))
        bc = m.group(6) is not None
        if dual_year is not None and calendar != "GREGORIAN":
            raise ValueError("Cannot use dual year (YYYY/YY) in non-Gregorian calendar: " + datestr)

        if calendar == "GREGORIAN":
            return GregorianDate(year, month, day, bc=bc, original=datestr, dual_year=dual_year)
        elif calendar == "JULIAN":
            return JulianDate(year, month, day, bc=bc, original=datestr)
        elif calendar == "FRENCH":
            return FrenchDate(year, month, day, bc=bc, original=datestr)
        elif calendar == "HEBREW":
            return HebrewDate(year, month, day, bc=bc, original=datestr)
        else:
            raise ValueError("Unknown calendar: " + datestr)

    def __lt__(self, other):
        return self.key() < other.key()

    def __le__(self, other):
        return self.key() <= other.key()

    def __eq__(self, other):
        return self.key() == other.key()

    def __ne__(self, other):
        return self.key() != other.key()

    def __gt__(self, other):
        return self.key() > other.key()

    def __ge__(self, other):
        return self.key() >= other.key()

    def fmt(self):
        """Make printable representation out of this instance.
        """
        val = [self.day, self.month, self.year_str]
        return " ".join([str(item) for item in val if item is not None])

    def __str__(self):
        return "{}(year={}, month={}, day={}, bc={})".format(
            self.__class__.__name__, self.year, self.month,
            self.day, self.bc)

    def __repr__(self):
        return str(self)


class GregorianDate(CalendarDate):
    """Implementation of CalendarDate for Gregorian calendar.

    In GEDCOM Gregorian calendar dates are allowed to specify year in the
    form YEAR1/YEAR2 (a.k.a.) dual-dating. Second number is used to specify
    year as if calendar year starts in January, while the first number is
    used for actual calendar year which starts at different date. Note that
    GEDCOM specifies that dual year uses just two last digits in the dual
    year number, though some implementations use 4 digits. This class expects
    actual year number (e.g. as if it was specified as "1699/1700").

    Parameter ``dual_year`` (and corresponding attribute) is used for dual
    year. Other parameters have the same meaning as in :py:class:`CalendarDate`
    class.

    :param int dual_year: Dual year number or ``None``. Actual year should be
        given, not just two last digits.
    """
    def __init__(self, year, month=None, day=None, bc=False, original=None, dual_year=None):
        CalendarDate.__init__(self, year, month, day, bc, original)
        self.dual_year = dual_year
        """If not ``None`` then this number represent year in a calendar with
        year starting on January 1st (`int`).
        """

    @classmethod
    def months(self):
        """Ordered list of month names (in GEDCOM format) defined in calendar.
        """
        return MONTHS_GREG

    @property
    def calendar(self):
        """Calendar name used for this date, in format defined by GEDCOM
        (`str`)
        """
        return "GREGORIAN"

    def key(self):
        """Return ordering key for this instance.
        """
        # In dual dating use second year
        year = self.dual_year if self.dual_year is not None else self.year
        if self.bc:
            year = - year
        month = self.month_num
        day = self.day
        offset = 0.
        if self.month_num is None:
            # Take Jan 1 as next year
            year += 1
            month = 1
            day = 1
            offset = 1.
        elif self.day is None:
            month += 1
            if month == 13:
                month -= 12
                year += 1
            day = 1
            offset = 1.
        jd = convertdate.gregorian.to_jd(year, month, day) - offset

        flag = 1 if self.day is None or self.month_num is None else 0
        return jd, flag

    @property
    def year_str(self):
        """Calendar year in string representation, this can include dual year
        and/or B.C. suffix (`str`)
        """
        year = str(self.year)
        if self.dual_year is not None:
            year += "/" + str(self.dual_year)[-2:]
        if self.bc:
            year += " B.C."
        return year

    def fmt(self):
        """Make printable representation out of this instance.
        """
        val = [self.day, self.month, self.year_str]
        return " ".join([str(item) for item in val if item is not None])


class JulianDate(CalendarDate):
    """Implementation of CalendarDate for Julian calendar.

    All parameters have the same meaning as in :py:class:`CalendarDate` class.
    """
    def __init__(self, year, month=None, day=None, bc=False, original=None):
        CalendarDate.__init__(self, year, month, day, bc, original)

    @classmethod
    def months(self):
        """Ordered list of month names (in GEDCOM format) defined in calendar.
        """
        return MONTHS_GREG

    def key(self):
        """Return ordering key for this instance.
        """
        year = - self.year if self.bc else self.year
        month = self.month_num
        day = self.day
        offset = 0.
        if self.month_num is None:
            # Take Jan 1 as next year
            year += 1
            month = 1
            day = 1
            offset = 1.
        elif self.day is None:
            month += 1
            if month == 13:
                month -= 12
                year += 1
            day = 1
            offset = 1.
        jd = convertdate.julian.to_jd(year, month, day) - offset

        flag = 1 if self.day is None or self.month_num is None else 0
        return jd, flag

    @property
    def calendar(self):
        """Calendar name used for this date, in format defined by GEDCOM
        (`str`)
        """
        return "JULIAN"


class HebrewDate(CalendarDate):
    """Implementation of CalendarDate for Hebrew calendar.

    All parameters have the same meaning as in :py:class:`CalendarDate` class.
    """
    def __init__(self, year, month=None, day=None, bc=False, original=None):
        CalendarDate.__init__(self, year, month, day, bc, original)

    @classmethod
    def months(self):
        """Ordered list of month names (in GEDCOM format) defined in calendar.
        """
        return MONTHS_HEBR

    def key(self):
        """Return ordering key for this instance.
        """
        calendar = convertdate.hebrew
        year = - self.year if self.bc else self.year
        month = self.month_num or convertdate.hebrew.year_months(year)
        day = self.day if self.day is not None else calendar.month_days(year, month)
        jd = calendar.to_jd(year, month, day)
        flag = 1 if self.day is None or self.month_num is None else 0
        return jd, flag

    @property
    def calendar(self):
        """Calendar name used for this date, in format defined by GEDCOM
        (`str`)
        """
        return "HEBREW"


class FrenchDate(CalendarDate):
    """Implementation of CalendarDate for French republican calendar.

    All parameters have the same meaning as in :py:class:`CalendarDate` class.
    """
    def __init__(self, year, month=None, day=None, bc=False, original=None):
        CalendarDate.__init__(self, year, month, day, bc, original)

    @classmethod
    def months(self):
        """Ordered list of month names (in GEDCOM format) defined in calendar.
        """
        return MONTHS_FREN

    def key(self):
        """Return ordering key for this instance.
        """
        calendar = convertdate.french_republican
        year = - self.year if self.bc else self.year
        month = self.month_num or 13
        day = self.day
        if day is None:
            if month == 13:
                # very short "month"
                day = 5
            else:
                day = 30
        jd = calendar.to_jd(year, month, day)
        flag = 1 if self.day is None or self.month_num is None else 0
        return jd, flag

    @property
    def calendar(self):
        """Calendar name used for this date, in format defined by GEDCOM
        (`str`)
        """
        return "FRENCH R"


class OldCalendarDate(object):
    """Representation of calendar date, corresponding to <DATE> element.

    This includes optional calendar kind (calendar escape) which can be
    one of @#DHEBREW@ | @#DROMAN@ | @#DFRENCH R@ | @#DGREGORIAN@ |
    @#DJULIAN@ | @#DUNKNOWN@ (@#DGREGORIAN@ is default). Date consists
    of year, month, and day; day and month are optional (either day or
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
        return GregorianDate(2999)

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
