"""Module for parsing and representing dates in gedcom format.
"""

from __future__ import print_function, absolute_import, division

__all__ = [
    "CalendarTypes", "CalendarDate", "FrenchDate", "GregorianDate",
    "HebrewDate", "JulianDate", "DateValueTypes", "DateValue",
    "DateValueAbout", "DateValueAfter", "DateValueBefore", "DateValueCalculated",
    "DateValueEstimated", "DateValueFrom", "DateValueInterpreted", "DateValuePeriod",
    "DateValuePhrase", "DateValueRange", "DateValueSimple", "DateValueTo", "DateValueTypes",
    "CalendarDateVisitor", "DateValueVisitor"
]

import abc
import re
from six import with_metaclass

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
DATE = r"""
    (?:@\#D([\w ]+)@\s+)?       # @#DCALENDAR@, optional (group=1)
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

# (<DATE_PHRASE>)
DATE_PHRASE = r"^\((?P<phrase>.*)\)$"

# <DATE>
DATE_SIMPLE = r"^(?P<date>" + DATE + ")$"


class CalendarTypes(object):
    """Namespace for constants defining names of calendars.

    Note that it does not define constants for ``ROMAN`` calendar which is
    declared in GEDCOM standrad as a placeholder for future definition, or
    ``UNKNOWN`` calendar which is not supported by this library.
    """
    GREGORIAN = "GREGORIAN"
    JULIAN = "JULIAN"
    HEBREW = "HEBREW"
    FRENCH_R = "FRENCH R"


class CalendarDate(with_metaclass(abc.ABCMeta)):
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
    @abc.abstractmethod
    def months(self):
        """Ordered list of month names (in GEDCOM format) defined in calendar.
        """
        raise NotImplementedError()

    @abc.abstractmethod
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
    @abc.abstractmethod
    def calendar(self):
        """Calendar name used for this date, one of the constants defined in
        :class:`CalendarTypes` (`str`)
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def accept(self, visitor):
        """Support visitor pattern.

        Each concrete sub-class will implement this method by dispatching the
        call to corresponding visitor method.

        :param CalendarDateVisitor visitor: visitor instance.
        :returns: Value returned from a visitor method.
        """
        raise NotImplementedError()

    @classmethod
    def parse(cls, datestr):
        """Parse <DATE> string and make :class:`CalendarDate` from it.

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

        calendar = m.group(1) or CalendarTypes.GREGORIAN
        day = None if m.group(2) is None else int(m.group(2))
        month = m.group(3)
        year = int(m.group(4))
        dual_year = _dual_year(m.group(4), m.group(5))
        bc = m.group(6) is not None
        if dual_year is not None and calendar != CalendarTypes.GREGORIAN:
            raise ValueError("Cannot use dual year (YYYY/YY) in non-Gregorian calendar: " + datestr)

        if calendar == CalendarTypes.GREGORIAN:
            return GregorianDate(year, month, day, bc=bc, original=datestr, dual_year=dual_year)
        elif calendar == CalendarTypes.JULIAN:
            return JulianDate(year, month, day, bc=bc, original=datestr)
        elif calendar == CalendarTypes.FRENCH_R:
            return FrenchDate(year, month, day, bc=bc, original=datestr)
        elif calendar == CalendarTypes.HEBREW:
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
    year. Other parameters have the same meaning as in :class:`CalendarDate`
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
        return CalendarTypes.GREGORIAN

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

    def accept(self, visitor):
        return visitor.visitGregorian(self)


class JulianDate(CalendarDate):
    """Implementation of CalendarDate for Julian calendar.

    All parameters have the same meaning as in :class:`CalendarDate` class.
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
        return CalendarTypes.JULIAN

    def accept(self, visitor):
        return visitor.visitJulian(self)


class HebrewDate(CalendarDate):
    """Implementation of CalendarDate for Hebrew calendar.

    All parameters have the same meaning as in :class:`CalendarDate` class.
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
        return CalendarTypes.HEBREW

    def accept(self, visitor):
        return visitor.visitHebrew(self)


class FrenchDate(CalendarDate):
    """Implementation of CalendarDate for French republican calendar.

    All parameters have the same meaning as in :class:`CalendarDate` class.
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
        return CalendarTypes.FRENCH_R

    def accept(self, visitor):
        return visitor.visitFrench(self)


class CalendarDateVisitor(with_metaclass(abc.ABCMeta)):
    """Interface for implementation of Visitor pattern for
    :class:`CalendarDate` classes.

    One can easily extend behavior of the :class:`CalendarDate` class
    hierarchy without modifying classes themselves. Clients need to implement
    new behavior by sub-classing :class:`CalendarDateVisitor` and calling
    :meth:`CalendarDate.accept()` method, e.g.::

        class FormatterVisitor(CalendarDateVisitor):

            def visitGregorian(self, date):
                return "Gregorian date:" + date.fmt()

            # and so on for each date type

        visitor = FormatterVisitor()

        date = CalendarDate.parse(date_string)
        formatted = date.accept(visitor)
    """

    def visitGregorian(self, date):
        """Visit an instance of :class:`GregorianDate` type.
        """
        raise NotImplementedError()

    def visitJulian(self, date):
        """Visit an instance of :class:`JulianDate` type.
        """
        raise NotImplementedError()

    def visitHebrew(self, date):
        """Visit an instance of :class:`HebrewDate` type.
        """
        raise NotImplementedError()

    def visitFrench(self, date):
        """Visit an instance of :class:`FrenchDate` type.
        """
        raise NotImplementedError()


class DateValueTypes(object):
    """Namespace for constants defining types of date values.
    """

    SIMPLE = 0
    "Date value consists of a single CalendarDate"

    FROM = 1
    "Period of dates starting at specified date, end date is unknown"

    TO = 2
    "Period of dates ending at specified date, start date is unknown"

    PERIOD = 3
    "Period of dates starting at one date and ending at another"

    BEFORE = 4
    "Date value for an event known to happen before given date"

    AFTER = 5
    "Date value for an event known to happen after given date"

    RANGE = 6
    "Date value for an event known to happen between given dates"

    ABOUT = 7
    "Date value for an event known to happen at approximate date"

    CALCULATED = 8
    "Date value for an event calculated from other known information"

    ESTIMATED = 9
    "Date value for an event estimated from other known information"

    INTERPRETED = 10
    "Date value for an event interpreted from a specified phrase"

    PHRASE = 11
    "Date value for an event is a phrase"


class DateValue(with_metaclass(abc.ABCMeta)):
    """Representation of the <DATE_VALUE>, can be exact date, range,
    period, etc.

    ``DateValue`` is an abstract base class, for each separate kind of GEDCOM
    date there is a separate concrete class (e.g. ``DateValueRange``). Class
    method :meth:`parse` is used to parse a date string and return an
    instance corresponding DateValue type. Different types have different
    attributes, to implement type-specific code on client side one can use one
    of these approaches:

        - dispatch based on the value of :attr:`kind` attribute, it has one of
          the values defined in :class:`DateValueTypes` enum,
        - dispatch based on the type of the instance using ``isinstance``
          method to check the type (e.g. ``isinstance(date, DateValueRange)``)
        - double dispatch (visitor pattern) by implementing
          :class:`DateValueVisitor` interface.

    :param key: Object that is used for ordering, usually
            :class:`CalendarDate` but can be ``None``.
    """
    def __init__(self, key):
        self._key = key

    @classmethod
    def parse(cls, datestr):
        """Parse string <DATE_VALUE> string and make :class:`DateValue`
        instance out of it.

        :param str datestr: String with GEDCOM date, range, period, etc.
        """
        # some apps generate DATE recods without any value, which is
        # non-standard, return empty DateValue for those
        if not datestr:
            return DateValuePhrase(None)
        for regex, klass in DATES:
            m = regex.match(datestr)
            if m is not None:
                groups = {}
                for key, val in m.groupdict().items():
                    if key != 'phrase':
                        val = CalendarDate.parse(val)
                    groups[key] = val
                return klass(**groups)
        # if cannot parse string assume it is a phrase
        return DateValuePhrase(datestr)

    @property
    @abc.abstractmethod
    def kind(self):
        """The type of GEDCOM date, one of the constants defined in
        :class:`DateValueTypes`.
        """
        raise NotImplementedError()

    def key(self):
        """Return ordering key for this instance.

        If this instance has a date or range of dates associated with it then
        this method returns first or only date associated with this instance.
        For other dates (``PHRASE`` is the only instance without date) it
        returns a fixed but arbitrary date in the future.
        """
        if self._key is None:
            # Use year 2999 so that it is ordered after all real dates
            return GregorianDate(2999)
        return self._key

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

    @abc.abstractmethod
    def accept(self, visitor):
        """Support visitor pattern.

        Each concrete sub-class will implement this method by dispatching the
        call to corresponding visitor method.

        :param DateValueVisitor visitor: visitor instance.
        :returns: Value returned from a visitor method.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def fmt(self):
        """Return date as a string formatted similarly to its GEDCOM
        representation.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return str(self)


class _DateValueSingle(DateValue):
    """Implementation of DateValue for single-value date.
    """
    def __init__(self, date):
        DateValue.__init__(self, date)
        self._date = date

    @property
    def date(self):
        "Date of this instance (`CalendarDate`)"
        return self._date

    def __str__(self):
        return "{}(date={})".format(self.__class__.__name__, self.date)


class _DateValueDual(DateValue):
    """Implementation of DateValue for dual-value date.
    """
    def __init__(self, date1, date2):
        DateValue.__init__(self, date1)
        self._date1 = date1
        self._date2 = date2

    @property
    def date1(self):
        "First date of this instance (`CalendarDate`)"
        return self._date1

    @property
    def date2(self):
        "Second date of this instance (`CalendarDate`)"
        return self._date2

    def __str__(self):
        return "{}(date1={}, date2={})".format(self.__class__.__name__, self.date1, self.date2)


class DateValueSimple(_DateValueSingle):
    """Implementation of DateValue for simple single-value DATE.
    """
    @property
    def kind(self):
        return DateValueTypes.SIMPLE

    def accept(self, visitor):
        return visitor.visitSimple(self)

    def fmt(self):
        return self.date.fmt()


class DateValueFrom(_DateValueSingle):
    """Implementation of DateValue for FROM date.
    """
    @property
    def kind(self):
        return DateValueTypes.FROM

    def accept(self, visitor):
        return visitor.visitFrom(self)

    def fmt(self):
        return "FROM {}".format(self.date.fmt())


class DateValueTo(_DateValueSingle):
    """Implementation of DateValue for TO date.
    """
    @property
    def kind(self):
        return DateValueTypes.TO

    def accept(self, visitor):
        return visitor.visitTo(self)

    def fmt(self):
        return "TO {}".format(self.date.fmt())


class DateValuePeriod(_DateValueDual):
    """Implementation of DateValue for FROM ... TO date.
    """
    @property
    def kind(self):
        return DateValueTypes.PERIOD

    def accept(self, visitor):
        return visitor.visitPeriod(self)

    def fmt(self):
        return "FROM {} TO {}".format(self.date1.fmt(), self.date2.fmt())


class DateValueBefore(_DateValueSingle):
    """Implementation of DateValue for BEF date.
    """
    @property
    def kind(self):
        return DateValueTypes.BEFORE

    def accept(self, visitor):
        return visitor.visitBefore(self)

    def fmt(self):
        return "BEFORE {}".format(self.date.fmt())


class DateValueAfter(_DateValueSingle):
    """Implementation of DateValue for AFTE date.
    """
    @property
    def kind(self):
        return DateValueTypes.AFTER

    def accept(self, visitor):
        return visitor.visitAfter(self)

    def fmt(self):
        return "AFTER {}".format(self.date.fmt())


class DateValueRange(_DateValueDual):
    """Implementation of DateValue for BET .. AND ... date.
    """
    @property
    def kind(self):
        return DateValueTypes.RANGE

    def accept(self, visitor):
        return visitor.visitRange(self)

    def fmt(self):
        return "BETWEEN {} AND {}".format(self.date1.fmt(), self.date2.fmt())


class DateValueAbout(_DateValueSingle):
    """Implementation of DateValue for ABT date.
    """
    @property
    def kind(self):
        return DateValueTypes.ABOUT

    def accept(self, visitor):
        return visitor.visitAbout(self)

    def fmt(self):
        return "ABOUT {}".format(self.date.fmt())


class DateValueCalculated(_DateValueSingle):
    """Implementation of DateValue for CAL date.
    """
    @property
    def kind(self):
        return DateValueTypes.CALCULATED

    def accept(self, visitor):
        return visitor.visitCalculated(self)

    def fmt(self):
        return "CALCULATED {}".format(self.date.fmt())


class DateValueEstimated(_DateValueSingle):
    """Implementation of DateValue for EST date.
    """
    @property
    def kind(self):
        return DateValueTypes.ESTIMATED

    def accept(self, visitor):
        return visitor.visitEstimated(self)

    def fmt(self):
        return "ESTIMATED {}".format(self.date.fmt())


class DateValueInterpreted(_DateValueSingle):
    """Implementation of DateValue for INT date.
    """
    def __init__(self, date, phrase):
        _DateValueSingle.__init__(self, date)
        self._phrase = phrase

    @property
    def kind(self):
        return DateValueTypes.INTERPRETED

    @property
    def phrase(self):
        """Phrase associated with this date (`str`)
        """
        return self._phrase

    def accept(self, visitor):
        return visitor.visitInterpreted(self)

    def __str__(self):
        return "{}(date={}, phrase={})".format(self.__class__.__name__, self.date, self.phrase)

    def fmt(self):
        return "INTERPRETED {} ({})".format(self.date.fmt(), self.phrase)


class DateValuePhrase(_DateValueSingle):
    """Implementation of DateValue for INT date.
    """
    def __init__(self, phrase):
        _DateValueSingle.__init__(self, None)
        self._phrase = phrase

    @property
    def kind(self):
        return DateValueTypes.PHRASE

    @property
    def phrase(self):
        """Phrase associated with this date (`str`)
        """
        return self._phrase

    def accept(self, visitor):
        return visitor.visitPhrase(self)

    def __str__(self):
        return "{}(phrase={})".format(self.__class__.__name__, self.phrase)

    def fmt(self):
        if self.phrase is None:
            return ""
        else:
            return "({})".format(self.phrase)


DATES = (
    (re.compile(DATE_PERIOD, re.X | re.I), DateValuePeriod),
    (re.compile(DATE_PERIOD_FROM, re.X | re.I), DateValueFrom),
    (re.compile(DATE_PERIOD_TO, re.X | re.I), DateValueTo),
    (re.compile(DATE_RANGE, re.X | re.I), DateValueRange),
    (re.compile(DATE_RANGE_BEFORE, re.X | re.I), DateValueBefore),
    (re.compile(DATE_RANGE_AFTER, re.X | re.I), DateValueAfter),
    (re.compile(DATE_APPROX_ABOUT, re.X | re.I), DateValueAbout),
    (re.compile(DATE_APPROX_CALC, re.X | re.I), DateValueCalculated),
    (re.compile(DATE_APPROX_EST, re.X | re.I), DateValueEstimated),
    (re.compile(DATE_INTERP, re.X | re.I), DateValueInterpreted),
    (re.compile(DATE_PHRASE, re.X | re.I), DateValuePhrase),
    (re.compile(DATE_SIMPLE, re.X | re.I), DateValueSimple),
)


class DateValueVisitor(with_metaclass(abc.ABCMeta)):
    """Interface for implementation of Visitor pattern for DateValue classes.

    One can easily extend behavior of the DateValue class hierarchy without
    modifying classes themselves. Clients need to implement new behavior by
    sub-classing ``DateValueVisitor`` and calling :meth:`DateValue.accept`
    method, e.g.::

        class FormatterVisitor(DateValueVisitor):

            def visitSimple(self, date):
                return "Simple date: " + date.date.fmt()

            # and so on for each date type

        visitor = FormatterVisitor()

        date = DateValue.parse(date_string)
        formatted = date.accept(visitor)
    """

    @abc.abstractmethod
    def visitSimple(self, date):
        """Visit an instance of :class:`DateValueSimple` type.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def visitPeriod(self, date):
        """Visit an instance of :class:`DateValuePeriod` type.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def visitFrom(self, date):
        """Visit an instance of :class:`DateValueFrom` type.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def visitTo(self, date):
        """Visit an instance of :class:`DateValueTo` type.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def visitRange(self, date):
        """Visit an instance of :class:`DateValueRange` type.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def visitBefore(self, date):
        """Visit an instance of :class:`DateValueBefore` type.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def visitAfter(self, date):
        """Visit an instance of :class:`DateValueAfter` type.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def visitAbout(self, date):
        """Visit an instance of :class:`DateValueAbout` type.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def visitCalculated(self, date):
        """Visit an instance of :class:`DateValueCalculated` type.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def visitEstimated(self, date):
        """Visit an instance of :class:`DateValueEstimated` type.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def visitInterpreted(self, date):
        """Visit an instance of :class:`DateValueInterpreted` type.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def visitPhrase(self, date):
        """Visit an instance of :class:`DateValuePhrase` type.
        """
        raise NotImplementedError()
