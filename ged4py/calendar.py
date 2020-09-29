"""Module for parsing and representing calendar dates in gedcom format.
"""

__all__ = [
    "CalendarTypes", "CalendarDate", "FrenchDate", "GregorianDate",
    "HebrewDate", "JulianDate", "CalendarDateVisitor",
]

import abc
import re

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

# DATE := [<DATE_CALENDAR_ESCAPE> | <NULL>] <DATE_CALENDAR>
# <DATE_CALENDAR> := [<YEAR> | <MONTH> <YEAR> | <DAY> <MONTH> <YEAR>]
# <YEAR can be specified as "1000B.C." or "1699/00"
# <MONTH> is all characters.
# This does not use named groups, it may appear few times in other expressions
# Groups: 1: calendar; 2: day; 3: month; 4: year
# Note: this definition is also used in date.py
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


class CalendarTypes(object):
    """Namespace for constants defining names of calendars.

    Note that it does not define constants for ``ROMAN`` calendar which is
    declared in GEDCOM standard as a placeholder for future definition, or
    ``UNKNOWN`` calendar which is not supported by this library.

    The constants defined in this namespace are used for the values of the
    :attr:`CalendarDate.calendar` attribute. Each separate class implementing
    :class:`CalendarDate` interface uses distinct value for that attribute,
    and this value can be used to deduce actual type of the
    :class:`CalendarDate` instance.
    """

    GREGORIAN = "GREGORIAN"
    """This is the value assigned to :attr:`GregorianDate.calendar` attribute.
    """

    JULIAN = "JULIAN"
    """This is the value assigned to :attr:`JulianDate.calendar` attribute.
    """

    HEBREW = "HEBREW"
    """This is the value assigned to :attr:`HebrewDate.calendar` attribute.
    """

    FRENCH_R = "FRENCH R"
    """This is the value assigned to :attr:`FrenchDate.calendar` attribute.
    """


class CalendarDate(metaclass=abc.ABCMeta):
    """Interface for calendar date representation.

    :param int year: Calendar year number. If ``bc`` parameter is ``True``
        then this year is before "epoch" of that calendar.
    :param str month: Name of the month. Optional, but if day is given then
        month cannot be None.
    :param int day: Day in a month, optional.
    :param bool bc: `True` if year has "B.C."
    :param str original: Original string representation of this date as it was
        specified in GEDCOM file, could be ``None``.

    This class defines attributes and methods that are common for all
    calendars defined in GEDCOM (though the meaning and representation can be
    different in different calendars). In GEDCOM date consists of year, month,
    and day; day and month are optional (either day or day+month), year must
    be present. Day is a number, month is month name in a given calendar.
    Year is a number optionally followed by ``B.C.`` or ``/NUMBER`` (latter
    is defined for Gregorian calendar only).

    Implementation for different calendars are provided by subclasses which
    can implement additional attributes or methods. All subclasses need to
    implement :meth:`key` method to support ordering of the dates from
    different calendars. There are presently four implementations defined
    in this module:

        - :class:`GregorianDate` for "GREGORIAN" calendar
        - :class:`JulianDate` for "JULIAN" calendar
        - :class:`HebrewDate` for "HEBREW" calendar
        - :class:`FrenchDate` for "FRENCH R" calendar

    To implement type-specific code on client side one can use one of these
    approaches:

        - dispatch based on the value of :attr:`calendar` attribute, it has
          one of the values defined in :class:`CalendarTypes` namespace,
          the value maps uniquely to an implementation class;
        - dispatch based on the type of the instance using ``isinstance``
          method to check the type (e.g. ``isinstance(date, GregorianDate)``);
        - double dispatch (visitor pattern) by implementing
          :class:`CalendarDateVisitor` interface.
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
        """Implementation of visitor pattern.

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
        :returns: :class:`CalendarDate` instance
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

    def __hash__(self):
        return hash(self.key())

    def __str__(self):
        """Make printable representation out of this instance.
        """
        val = [self.day, self.month, self.year_str]
        if self.calendar != CalendarTypes.GREGORIAN:
            val = ["@#D{}@".format(self.calendar)] + val
        return " ".join([str(item) for item in val if item is not None])

    def __repr__(self):
        return str(self)


class GregorianDate(CalendarDate):
    """Implementation of :class:`CalendarDate` for Gregorian calendar.

    Parameter ``dual_year`` (and corresponding attribute) is used for dual
    year. Other parameters have the same meaning as in :class:`CalendarDate`
    class.

    :param int dual_year: Dual year number or ``None``. Actual year should be
        given, not just two last digits.

    In GEDCOM Gregorian calendar dates are allowed to specify year in the
    form YEAR1/YEAR2 (a.k.a.) dual-dating. Second number is used to specify
    year as if calendar year starts in January, while the first number is
    used for actual calendar year which starts at different date. Note that
    GEDCOM specifies that dual year uses just two last digits in the dual
    year number, though some implementations use 4 digits. This class expects
    actual year number (e.g. as if it was specified as "1699/1700").
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
        """Calendar name used for this date, for GregorianDate this is always
        :attr:`CalendarTypes.GREGORIAN` (`str`)
        """
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

    def __str__(self):
        """Make printable representation out of this instance.
        """
        val = [self.day, self.month, self.year_str]
        return " ".join([str(item) for item in val if item is not None])

    def accept(self, visitor):
        return visitor.visitGregorian(self)


class JulianDate(CalendarDate):
    """Implementation of :class:`CalendarDate` for Julian calendar.

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
        """Calendar name used for this date, for JulianDate this is always
        :attr:`CalendarTypes.JULIAN` (`str`)
        """
        return CalendarTypes.JULIAN

    def accept(self, visitor):
        return visitor.visitJulian(self)


class HebrewDate(CalendarDate):
    """Implementation of :class:`CalendarDate` for Hebrew calendar.

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
        """Calendar name used for this date, for HebrewDate this is always
        :attr:`CalendarTypes.HEBREW` (`str`)
        """
        return CalendarTypes.HEBREW

    def accept(self, visitor):
        return visitor.visitHebrew(self)


class FrenchDate(CalendarDate):
    """Implementation of :class:`CalendarDate` for French Republican calendar.

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
        """Calendar name used for this date, for FrenchDate this is always
        :attr:`CalendarTypes.FRENCH` (`str`)
        """
        return CalendarTypes.FRENCH_R

    def accept(self, visitor):
        return visitor.visitFrench(self)


class CalendarDateVisitor(metaclass=abc.ABCMeta):
    """Interface for implementation of Visitor pattern for
    :class:`CalendarDate` classes.

    One can easily extend behavior of the :class:`CalendarDate` class
    hierarchy without modifying classes themselves. Clients need to implement
    new behavior by sub-classing :class:`CalendarDateVisitor` and calling
    :meth:`CalendarDate.accept()` method, e.g.::

        class FormatterVisitor(CalendarDateVisitor):

            def visitGregorian(self, date):
                return "Gregorian date:" + str(date)

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
