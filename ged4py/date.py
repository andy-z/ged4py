"""Module for parsing and representing dates in gedcom format.
"""

from __future__ import print_function, absolute_import, division

__all__ = [
    "DateValueTypes", "DateValue",
    "DateValueAbout", "DateValueAfter", "DateValueBefore", "DateValueCalculated",
    "DateValueEstimated", "DateValueFrom", "DateValueInterpreted", "DateValuePeriod",
    "DateValuePhrase", "DateValueRange", "DateValueSimple", "DateValueTo",
    "DateValueVisitor"
]

import abc
import re
from six import with_metaclass

from .calendar import CalendarDate, GregorianDate, DATE

# DATE_VALUE := [
#     <DATE> |
#     <DATE_PERIOD> |
#     <DATE_RANGE>|
#     <DATE_APPROXIMATED> |
#     INT <DATE> (<DATE_PHRASE>) |
#     (<DATE_PHRASE>)
#     ]

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

# plus/minus infinity (kinda)
_START_OF_TIME = GregorianDate(5000, bc=True)
_END_OF_TIME = GregorianDate(5000)


class DateValueTypes(object):
    """Namespace for constants defining types of date values.

    The constants defined in this namespace are used for the values of the
    :attr:`DateValue.kind` attribute. Each separate class implementing
    :class:`DateValue` interface uses distinct value for that attribute,
    and this value can be used to deduce actual type of the date
    :class:`DateValue` instance.
    """

    SIMPLE = "SIMPLE"
    """Date value consists of a single CalendarDate, corresponding
    implementation class is :class:`DateValueSimple`.
    """

    FROM = "FROM"
    """Period of dates starting at specified date, end date is unknown,
    corresponding implementation class is :class:`DateValueFrom`
    """

    TO = "TO"
    """Period of dates ending at specified date, start date is unknown,
    corresponding implementation class is :class:`DateValueTo`.
    """

    PERIOD = "PERIOD"
    """Period of dates starting at one date and ending at another,
    corresponding implementation class is :class:`DateValuePeriod`.
    """

    BEFORE = "BEFORE"
    """Date value for an event known to happen before given date,
    corresponding implementation class is :class:`DateValueBefore`.
    """

    AFTER = "AFTER"
    """Date value for an event known to happen after given date,
    corresponding implementation class is :class:`DateValueAfter`.
    """

    RANGE = "RANGE"
    """Date value for an event known to happen between given dates,
    corresponding implementation class is :class:`DateValueRange`.
    """

    ABOUT = "ABOUT"
    """Date value for an event known to happen at approximate date,
    corresponding implementation class is :class:`DateValueAbout`.
    """

    CALCULATED = "CALCULATED"
    """Date value for an event calculated from other known information,
    corresponding implementation class is :class:`DateValueCalculated`.
    """

    ESTIMATED = "ESTIMATED"
    """Date value for an event estimated from other known information,
    corresponding implementation class is :class:`DateValueEstimated`.
    """

    INTERPRETED = "INTERPRETED"
    """Date value for an event interpreted from a specified phrase,
    corresponding implementation class is :class:`DateValueInterpreted`.
    """

    PHRASE = "PHRASE"
    """Date value for an event is a phrase, corresponding implementation
    class is :class:`DateValuePhrase`.
    """


class DateValue(with_metaclass(abc.ABCMeta)):
    """Representation of the <DATE_VALUE>, can be exact date, range,
    period, etc.

    :param key: Object that is used for ordering, usually it is a pair
            of :class:`~ged4py.calendar.CalendarDate` instances but can be
            ``None``.

    ``DateValue`` is an abstract base class, for each separate kind of GEDCOM
    date there is a separate concrete class. Class method :meth:`parse` is
    used to parse a date string and return an instance of corresponding
    sub-class of ``DateValue`` type.

    There are presently 12 concrete classes implementing this interface (e.g.
    :class:`DateValueSimple`, :class:`DateValueRange`, etc.) Different types
    have somewhat different set of attributes, to implement type-specific code
    on client side one can use one of these approaches:

        - dispatch based on the value of :attr:`kind` attribute, it has one of
          the values defined in :class:`DateValueTypes` namespace, and that
          value maps uniquely to a corresponding sub-class of
          :class:`DateValue`;
        - dispatch based on the type of the instance using ``isinstance``
          method to check the type (e.g.
          ``isinstance(date, DateValueRange)``);
        - double dispatch (visitor pattern) by implementing
          :class:`DateValueVisitor` interface.
    """
    def __init__(self, key):
        self._key = key

    @classmethod
    def parse(cls, datestr):
        """Parse string <DATE_VALUE> string and make :class:`DateValue`
        instance out of it.

        :param str datestr: String with GEDCOM date, range, period, etc.
        :returns: :class:`DateValue` instance
        """
        # In some cases date strings can have leadin/trailing spaces
        if datestr:
            datestr = datestr.strip()
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
        :class:`DateValueTypes` (`str`).
        """
        raise NotImplementedError()

    def key(self):
        """Return ordering key for this instance.

        If this instance has a range of dates associated with it then this
        method returns the range as pair of dates. If this instance has a
        single date associated with it then this method returns pair which
        includes the date twice. For other dates (``PHRASE`` is the only
        instance without date) it returns a a pair of fixed but arbitrary
        dates in the future.
        """
        if self._key is None:
            # Use _END_OF_TIME so that it is ordered after all real dates
            return _END_OF_TIME, _END_OF_TIME
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

    def __hash__(self):
        return hash(self.key())

    @abc.abstractmethod
    def accept(self, visitor):
        """Implementation of visitor pattern.

        Each concrete sub-class will implement this method by dispatching the
        call to corresponding visitor method.

        :param DateValueVisitor visitor: visitor instance.
        :returns: Value returned from a visitor method.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def __str__(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def __repr__(self):
        raise NotImplementedError()


class DateValueSimple(DateValue):
    """Implementation of :class:`DateValue` interface for simple single-value DATE.

    :param CalendarDate date: Corresponding date.
    """
    def __init__(self, date):
        DateValue.__init__(self, (date, date))
        self._date = date

    @property
    def kind(self):
        """For DateValueSimple class this is always
        :attr:`DateValueTypes.SIMPLE`.
        """
        return DateValueTypes.SIMPLE

    @property
    def date(self):
        "Calendar date corresponding to this instance (:class:`~ged4py.calendar.CalendarDate`)"
        return self._date

    def accept(self, visitor):
        return visitor.visitSimple(self)

    def __str__(self):
        return str(self.date)

    def __repr__(self):
        return "{}(date={})".format(self.__class__.__name__, self.date)


class DateValueFrom(DateValue):
    """Implementation of :class:`DateValue` interface for FROM date.

    :param CalendarDate date: Corresponding date.
    """
    def __init__(self, date):
        DateValue.__init__(self, (date, _END_OF_TIME))
        self._date = date

    @property
    def kind(self):
        """For DateValueFrom class this is always
        :attr:`DateValueTypes.FROM`.
        """
        return DateValueTypes.FROM

    @property
    def date(self):
        "Calendar date corresponding to this instance (:class:`~ged4py.calendar.CalendarDate`)"
        return self._date

    def accept(self, visitor):
        return visitor.visitFrom(self)

    def __str__(self):
        return "FROM {}".format(self.date)

    def __repr__(self):
        return "{}(date={})".format(self.__class__.__name__, self.date)


class DateValueTo(DateValue):
    """Implementation of :class:`DateValue` interface for TO date.

    :param CalendarDate date: Corresponding date.
    """
    def __init__(self, date):
        DateValue.__init__(self, (_START_OF_TIME, date))
        self._date = date

    @property
    def kind(self):
        """For DateValueTo class this is always
        :attr:`DateValueTypes.TO`.
        """
        return DateValueTypes.TO

    @property
    def date(self):
        "Calendar date corresponding to this instance (:class:`~ged4py.calendar.CalendarDate`)"
        return self._date

    def accept(self, visitor):
        return visitor.visitTo(self)

    def __str__(self):
        return "TO {}".format(self.date)

    def __repr__(self):
        return "{}(date={})".format(self.__class__.__name__, self.date)


class DateValuePeriod(DateValue):
    """Implementation of :class:`DateValue` interface for FROM ... TO date.

    :param CalendarDate date1: FROM date.
    :param CalendarDate date2: TO date.
    """
    def __init__(self, date1, date2):
        DateValue.__init__(self, (date1, date2))
        self._date1 = date1
        self._date2 = date2

    @property
    def kind(self):
        """For DateValuePeriod class this is always
        :attr:`DateValueTypes.PERIOD`.
        """
        return DateValueTypes.PERIOD

    @property
    def date1(self):
        "First Calendar date corresponding to this instance (:class:`~ged4py.calendar.CalendarDate`)"
        return self._date1

    @property
    def date2(self):
        "Second Calendar date corresponding to this instance (:class:`~ged4py.calendar.CalendarDate`)"
        return self._date2

    def accept(self, visitor):
        return visitor.visitPeriod(self)

    def __str__(self):
        return "FROM {} TO {}".format(self.date1, self.date2)

    def __repr__(self):
        return "{}(date1={}, date2={})".format(self.__class__.__name__, self.date1, self.date2)


class DateValueBefore(DateValue):
    """Implementation of :class:`DateValue` interface for BEF date.

    :param CalendarDate date: Corresponding date.
    """
    def __init__(self, date):
        DateValue.__init__(self, (_START_OF_TIME, date))
        self._date = date

    @property
    def kind(self):
        """For DateValueBefore class this is always
        :attr:`DateValueTypes.BEFORE`.
        """
        return DateValueTypes.BEFORE

    @property
    def date(self):
        "Calendar date corresponding to this instance (:class:`~ged4py.calendar.CalendarDate`)"
        return self._date

    def accept(self, visitor):
        return visitor.visitBefore(self)

    def __str__(self):
        return "BEFORE {}".format(self.date)

    def __repr__(self):
        return "{}(date={})".format(self.__class__.__name__, self.date)


class DateValueAfter(DateValue):
    """Implementation of :class:`DateValue` interface for AFT date.

    :param CalendarDate date: Corresponding date.
    """
    def __init__(self, date):
        DateValue.__init__(self, (date, _END_OF_TIME))
        self._date = date

    @property
    def kind(self):
        """For DateValueAfter class this is always
        :attr:`DateValueTypes.AFTER`.
        """
        return DateValueTypes.AFTER

    @property
    def date(self):
        "Calendar date corresponding to this instance (:class:`~ged4py.calendar.CalendarDate`)"
        return self._date

    def accept(self, visitor):
        return visitor.visitAfter(self)

    def __str__(self):
        return "AFTER {}".format(self.date)

    def __repr__(self):
        return "{}(date={})".format(self.__class__.__name__, self.date)


class DateValueRange(DateValue):
    """Implementation of :class:`DateValue` interface for BET ... AND ... date.

    :param CalendarDate date1: First date.
    :param CalendarDate date2: Second date.
    """
    def __init__(self, date1, date2):
        DateValue.__init__(self, (date1, date2))
        self._date1 = date1
        self._date2 = date2

    @property
    def kind(self):
        """For DateValueRange class this is always
        :attr:`DateValueTypes.RANGE`.
        """
        return DateValueTypes.RANGE

    @property
    def date1(self):
        "First Calendar date corresponding to this instance (:class:`~ged4py.calendar.CalendarDate`)"
        return self._date1

    @property
    def date2(self):
        "Second Calendar date corresponding to this instance (:class:`~ged4py.calendar.CalendarDate`)"
        return self._date2

    def accept(self, visitor):
        return visitor.visitRange(self)

    def __str__(self):
        return "BETWEEN {} AND {}".format(self.date1, self.date2)

    def __repr__(self):
        return "{}(date1={}, date2={})".format(self.__class__.__name__, self.date1, self.date2)


class DateValueAbout(DateValue):
    """Implementation of :class:`DateValue` interface for ABT date.

    :param CalendarDate date: Corresponding date.
    """
    def __init__(self, date):
        DateValue.__init__(self, (date, date))
        self._date = date

    @property
    def kind(self):
        """For DateValueAbout class this is always
        :attr:`DateValueTypes.ABOUT`.
        """
        return DateValueTypes.ABOUT

    @property
    def date(self):
        "Calendar date corresponding to this instance (:class:`~ged4py.calendar.CalendarDate`)"
        return self._date

    def accept(self, visitor):
        return visitor.visitAbout(self)

    def __str__(self):
        return "ABOUT {}".format(self.date)

    def __repr__(self):
        return "{}(date={})".format(self.__class__.__name__, self.date)


class DateValueCalculated(DateValue):
    """Implementation of :class:`DateValue` interface for CAL date.

    :param CalendarDate date: Corresponding date.
    """
    def __init__(self, date):
        DateValue.__init__(self, (date, date))
        self._date = date

    @property
    def kind(self):
        """For DateValueCalculated class this is always
        :attr:`DateValueTypes.CALCULATED`.
        """
        return DateValueTypes.CALCULATED

    @property
    def date(self):
        "Calendar date corresponding to this instance (:class:`~ged4py.calendar.CalendarDate`)"
        return self._date

    def accept(self, visitor):
        return visitor.visitCalculated(self)

    def __str__(self):
        return "CALCULATED {}".format(self.date)

    def __repr__(self):
        return "{}(date={})".format(self.__class__.__name__, self.date)


class DateValueEstimated(DateValue):
    """Implementation of :class:`DateValue` interface for EST date.

    :param CalendarDate date: Corresponding date.
    """
    def __init__(self, date):
        DateValue.__init__(self, (date, date))
        self._date = date

    @property
    def kind(self):
        """For DateValueEstimated class this is always
        :attr:`DateValueTypes.ESTIMATED`.
        """
        return DateValueTypes.ESTIMATED

    @property
    def date(self):
        "Calendar date corresponding to this instance (:class:`~ged4py.calendar.CalendarDate`)"
        return self._date

    def accept(self, visitor):
        return visitor.visitEstimated(self)

    def __str__(self):
        return "ESTIMATED {}".format(self.date)

    def __repr__(self):
        return "{}(date={})".format(self.__class__.__name__, self.date)


class DateValueInterpreted(DateValue):
    """Implementation of :class:`DateValue` interface for INT date.

    :param CalendarDate date: Corresponding date.
    :param str phrase: Phrase string associated with this date.
    """
    def __init__(self, date, phrase):
        DateValue.__init__(self, (date, date))
        self._date = date
        self._phrase = phrase

    @property
    def kind(self):
        """For DateValueInterpreted class this is always
        :attr:`DateValueTypes.INTERPRETED`.
        """
        return DateValueTypes.INTERPRETED

    @property
    def date(self):
        "Calendar date corresponding to this instance (:class:`~ged4py.calendar.CalendarDate`)"
        return self._date

    @property
    def phrase(self):
        """Phrase associated with this date (`str`)
        """
        return self._phrase

    def accept(self, visitor):
        return visitor.visitInterpreted(self)

    def __str__(self):
        return "INTERPRETED {} ({})".format(self.date, self.phrase)

    def __repr__(self):
        return "{}(date={}, phrase={})".format(self.__class__.__name__, self.date, self.phrase)


class DateValuePhrase(DateValue):
    """Implementation of :class:`DateValue` interface for phrase-date.

    :param str phrase: Phrase string associated with this date.
    """
    def __init__(self, phrase):
        DateValue.__init__(self, None)
        self._phrase = phrase

    @property
    def kind(self):
        """For DateValuePhrase class this is always
        :attr:`DateValueTypes.PHRASE`.
        """
        return DateValueTypes.PHRASE

    @property
    def phrase(self):
        """Phrase associated with this date (`str`)
        """
        return self._phrase

    def accept(self, visitor):
        return visitor.visitPhrase(self)

    def __str__(self):
        if self.phrase is None:
            return ""
        else:
            return "({})".format(self.phrase)

    def __repr__(self):
        return "{}(phrase={})".format(self.__class__.__name__, self.phrase)


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
    """Interface for implementation of Visitor pattern for :class:`DateValue`
    classes.

    One can easily extend behavior of the :class:`DateValue` class hierarchy
    without modifying classes themselves. Clients need to implement new
    behavior by sub-classing ``DateValueVisitor`` and calling
    :meth:`DateValue.accept` method, e.g.::

        class FormatterVisitor(DateValueVisitor):

            def visitSimple(self, date):
                return "Simple date: " + str(date.date)

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
