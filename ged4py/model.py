# -*- coding: utf-8 -*-

"""Module containing Python in-memory model for GEDCOM data.
"""

from __future__ import print_function, absolute_import, division

__all__ = ['make_record', 'Record', 'Pointer', 'NameRec', 'Name',
           'Date', 'Individual']

from .detail.name import (split_name, parse_name_altree, parse_name_ancestris,
                          parse_name_myher)
from .date import DateValue

# Even though the structure of GEDCOM file is more or less fixed,
# interpretation of some data may vary depending on which application
# produced GEDCOM file. Constants define different known dialect which
# are handled by classes below.
DIALECT_DEFAULT = "DEF"
DIALECT_MYHERITAGE = "MYHER"  # myheritage.com
DIALECT_ALTREE = "AGELONG"  # Agelong Tree (genery.com)
DIALECT_ANCESTRIS = "ANCESTRIS"  # Ancestris (ancestris.org)

# Names/Individuals can be ordered differently, e.g. by surname first,
# by given name first, or by maiden name first. This few constants define
# different ordering options.
ORDER_SURNAME_GIVEN = "last+first"
ORDER_GIVEN_SURNAME = "first+last"
ORDER_MAIDEN_GIVEN = "maiden+first"  # uses last name if no maiden name
ORDER_GIVEN_MAIDEN = "first+maiden"  # uses last name if no maiden name
ORDER_LIST = [ORDER_SURNAME_GIVEN, ORDER_GIVEN_SURNAME,
              ORDER_MAIDEN_GIVEN, ORDER_GIVEN_MAIDEN]


class Record(object):
    """Class representing a parsed GEDCOM record in a generic format.

    This is the main element of the data model, it represents records in
    GEDCOM files. Each GEDCOM records consists of small number of items:

    - level number, integer;
    - optional reference ID, string in format ``@identifier@``;
    - tag name, short string;
    - optional record value, arbitrary string, for pointer records
      the record value is the reference ID of some other record.

    For many record types GEDCOM specifies subordinate (nested) records with
    incremental level number.

    Record class defines an interface that makes it easier to navigate this
    complex hierarchy of subordinate and referenced records:

    - ``sub_records`` attribute contains the list of all immediate subordinate
      records of this record.
    - :py:meth:`sub_tag` method find subordinate record given its tag, it can
      do it recursively if tag name contains multiple levels separated by
      slashes, and it can navigate through the pointer records transparently
      if ``follow`` argument is ``True``.
    - :py:meth:`sub_tag_value` is a convenience method that finds a
      subordinate record (via :py:meth:`~Record.sub_tag` call) but returns
      value of the record instead of record itself. This simplifies handling
      of missing tags.
    - :py:meth:`sub_tags` returns the list of immediate subordinate records
      (no recursion). It is useful when multiple sub-records with the same tag
      can exist.

    There are few sub-classes of the ``Record`` class providing additional
    methods or facilities for specific tag types.

    In general it is impossible to define what constitutes value or identity
    of GEDCOM record, so comparison of the records does not make sense.
    Similarly hashing operation cannot be used on Record instances, and the
    class is explicitly marked as non-hashable.

    Client code usually does not need to create instances of this class
    directly, :py:meth:`make_record` should be used instead. If you create
    an instance of this class (or its subclass) then you are responsible for
    filling its attributes.

    :ivar int level: Record level number
    :ivar str xref_id: Record reference ID, possibly empty.
    :ivar str tag: Tag name
    :ivar object value: Record value, possibly None, for many record types
        value is a string or None, some subclasses can define different type
        of record value.
    :ivar list sub_records: List of subordinate records, possibly empty
    :ivar int offset: Record location in a file
    :ivar dialect: GEDCOM source dialect, one of the DIALECT_* values
    """
    def __init__(self):
        self.level = None
        self.xref_id = None
        self.tag = None
        self.value = None
        self.sub_records = None
        self.offset = None
        self.dialect = None

    def freeze(self):
        """Method called by parser when updates to this record finish.

        :return: self
        """
        return self

    def sub_tag(self, path, follow=True):
        """Finds and returns sub-record with given tag name.

        Path can be a simple tag name, in which case the first direct
        sub-record of this record with the matching tag is returned. Path
        can also consist of several tags separated by slashes, in that case
        sub-records are searched recursively.

        If ``follow`` is True then pointer records are resolved and pointed
        record is used instead of pointer record, this also works for all
        intermediate records in a path.

        :param str path: One or more tag names separated by slashes.
        :param boolean follow: If True then resolve pointers.
        :return: :py:class:`Record` instance or ``None`` if sub-record with a
            given tag does not exist.
        """
        tags = path.split('/')
        rec = self
        for tag in tags:
            recs = [x for x in (rec.sub_records or []) if x.tag == tag]
            if not recs:
                return None
            rec = recs[0]
            if follow and isinstance(rec, Pointer):
                rec = rec.ref
        return rec

    def sub_tag_value(self, path, follow=True):
        """Returns value of a direct sub-record.

        Works as :py:meth:`sub_tag` but returns value of a sub-record
        instead of sub-record itself.

        :param str path: tag names separated by slashes.
        :param boolean follow: If True then resolve pointers.
        :return: String or `None` if sub-record with a given
            tag does not exist.
        """
        rec = self.sub_tag(path, follow)
        if rec:
            return rec.value
        return None

    def sub_tags(self, *tags, **kw):
        """Returns list of immediate sub-records matching any tag name.

        Unlike :py:meth:`sub_tag` method this method does not support
        hierarchical paths. It resolves pointer records if ``follow``
        keyword argument is ``True`` (default).

        :param str tags: Names of the sub-record tag
        :param kw: Keyword arguments, only recognized keyword is `follow`
            with the same meaning as in :py:meth:`sub_tag`.
        :return: List of `Records`, possibly empty.
        """
        records = [x for x in self.sub_records if x.tag in tags]
        if kw.get('follow', True):
            records = [rec.ref if isinstance(rec, Pointer) else rec
                       for rec in records]
        return records

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        value = self.value
        if isinstance(value, (type(""), type(u""))) and len(value) > 32:
            value = value[:32] + "..."
        n_sub = 0 if self.sub_records is None else len(self.sub_records)
        if self.xref_id:
            fmt = "{0}(level={1.level}, xref_id={1.xref_id}, tag={1.tag}, " \
                "value={2!r}, offset={1.offset}, #subrec={3})"
        else:
            fmt = "{0}(level={1.level}, tag={1.tag}, " \
                "value={2!r}, offset={1.offset}, #subrec={3})"
        return fmt.format(self.__class__.__name__, self, value, n_sub)

    # Records cannot be hashed
    __hash__ = None


class Pointer(Record):
    """Sub-class of :py:class:`Record` representing a pointer to a record in
    a GEDCOM file.

    This class wraps a GEDCOM pointer value and adds a ``ref`` property which
    retrieves pointed object. Instance of this class will be used in place of
    the GEDCOM pointers in the objects created by parser.

    :param parser: Instance of `GedcomReader` class.

    :ivar str value: Value of the GEDCOM pointer (e.g. "@I1234@")
    :ivar Record ref: Pointed GEDCOM record
    """

    def __init__(self, parser):
        Record.__init__(self)
        self.parser = parser
        self._value = []  # use non-None to signify non-initialized

    @property
    def ref(self):
        if self._value == []:
            offset, _ = self.parser.xref0.get(self.value, (None, None))
            if offset is None:
                self._value = None
            else:
                self._value = self.parser.read_record(offset)
        return self._value


class NameRec(Record):
    """Sub-class of :py:class:`Record` representing the NAME record.

    This class adds an additional method for determining type of the name.
    It also redefines the type of the `value` attribute, it's type is tuple.
    Value tuple can contain 3 or 4 elements, if there are 4 elements then
    last element is a maiden name. Second element of a tuple is surname,
    first and third elements are pieces of the given name (this is determined
    entirely by how name is represented in GEDCOM file). Any of the elements
    can be empty string. If NAME record value is empty in GEDCOM file then
    all three fields of the tuple will be empty strings. Few examples::

        ("John", "Smith", "")
        ("Mary Joan", "Smith", "", "Ivanova")    # maiden name
        ("", "Ivanov", "Ivan Ivanovich")
        ("John", "Smith", "Jr.")
        ("", "", "")                             # empty NAME record

    Client code usually does not need to create instances of this class
    directly, :py:meth:`make_record` should be used instead.
    """

    def __init__(self):
        Record.__init__(self)

    def freeze(self):
        """Method called by parser when updates to this record finish.

        :return: self
        """
        # None is the same as empty string
        if self.value is None:
            self.value = ""
        if self.dialect in [DIALECT_ALTREE]:
            name_tuple = parse_name_altree(self)
        elif self.dialect in [DIALECT_MYHERITAGE]:
            name_tuple = parse_name_myher(self)
        elif self.dialect in [DIALECT_ANCESTRIS]:
            name_tuple = parse_name_ancestris(self)
        else:
            name_tuple = split_name(self.value)
        self.value = name_tuple
        return self

    @property
    def type(self):
        """Name type as defined in TYPE record. ``None`` if TYPE record is
        missing, otherwise string, e.g. "aka", "birth", "immigrant",
        "maiden", "married" (or anything else).
        """
        # +1 TYPE <NAME_TYPE> {0:1}
        rec = self.sub_tag("TYPE")
        return rec.value if rec else None

    def __str__(self):
        return Record.__str__(self)


class Name(object):
    """Class representing "summary" of person names.

    Person in GEDCOM can have multiple NAME records, e.g. "aka" name,
    "maiden" name, etc. This class provides simple interface for selecting
    "best" name from all existing names. The algorithm for choosing best
    options is:

    - If there are no NAME records then it makes an empty name (with all empty
      components)
    - If there is only one NAME record then it is used for person name.
    - If there are multiple NAME records then the first record without TYPE
      sub-record is used, or if all records have TYPE sub-records then first
      NAME record is used.

    :param list names: List of NAME records (:py:class:`NameRec` instances).
    :param dialect: One of ``DIALECT_*`` constants.
    """

    def __init__(self, names, dialect):
        self._names = names
        self._dialect = dialect
        self._primary = None  # "primary" name record

        if len(names) == 0:
            # make fake name record to simplify logic below
            self._primary = make_record(0, '', "NAME", "",
                                        [], 0, DIALECT_DEFAULT).freeze()
        elif len(names) == 1:
            self._primary = names[0]
        else:
            for name in names:
                if not name.type:
                    self._primary = name
                    break
            else:
                self._primary = names[0]

    @property
    def surname(self):
        """Person surname (``str``)"""
        return self._primary.value[1]

    @property
    def given(self):
        """Given name could include both first and middle name (``str``)"""
        if self._primary.value[0] and self._primary.value[2]:
            return self._primary.value[0] + ' ' + self._primary.value[2]
        return self._primary.value[0] or self._primary.value[2]

    @property
    def first(self):
        """First name is the first part of a given name (drops middle name)"""
        given = self.given
        if given:
            return given.split()[0]
        return given

    @property
    def maiden(self):
        """Maiden last name, can be None (``str``)"""
        if self._dialect == DIALECT_DEFAULT:
            # for default/unknown dialect try "maiden" name record first
            for name in self._names:
                if name.type == "maiden":
                    return name.value[1]
        # rely on NameRec extracting it from other source
        if self._primary and len(self._primary.value) > 3:
            return self._primary.value[3]
        return None

    def order(self, order):
        """Returns name order key.

        Returns tuple with two strings that can be compared to other such
        tuple obtained from different name. Note that if you want
        locale-dependent ordering then you need to compare strings using
        locale-aware method (e.g. ``locale.strxfrm``).

        :param order: One of the ``ORDER_*`` constants.
        :returns: tuple of two strings
        """
        given = self.given
        surname = self.surname
        if order in (ORDER_MAIDEN_GIVEN, ORDER_GIVEN_MAIDEN):
            surname = self.maiden or self.surname

        # We are collating empty names to come after non-empty,
        # so instead of empty we return "2" and add "1" as prefix to others
        given = ("1" + given) if given else "2"
        surname = ("1" + surname) if surname else "2"

        if order in (ORDER_SURNAME_GIVEN, ORDER_MAIDEN_GIVEN):
            return (surname, given)
        elif order in (ORDER_GIVEN_SURNAME, ORDER_GIVEN_MAIDEN):
            return (given, surname)
        else:
            raise ValueError("unexpected order: {}".format(order))

    def format(self):
        """Format name for output.

        There is no single correct way to represent name, values returned from
        this method are only useful in limited context, e.g. for logging.

        :return: Formatted name representation.
        """
        name = self._primary.value[0]
        if self.surname:
            if name:
                name += ' '
            name += self.surname
        if self._primary.value[2]:
            if name:
                name += ' '
            name += self._primary.value[2]
        return name

    def __str__(self):
        fmt = "{0}({1!r})"
        return fmt.format(self.__class__.__name__, self.format())


class Date(Record):
    """Sub-class of :py:class:`Record` representing the DATE record.

    After `freeze()` method is called by parser the `value` attribute contains
    instance of :py:class:`ged4py.date.DateValue` class.
    """
    def __init__(self):
        Record.__init__(self)

    def freeze(self):
        """Method called by parser when updates to this record finish.

        :return: self
        """
        self.value = DateValue.parse(self.value)
        return self


class Individual(Record):
    """Sub-class of :py:class:`Record` representing the INDI record.

    INDI record represents a single person in GEDCOM. This class defines
    few methods that are useful shortcuts for accessing person information,
    such as navigation to parent records, name, etc.

    Client code usually does not need to create instances of this class
    directly, :py:meth:`make_record` should be used instead.
    """
    def __init__(self):
        Record.__init__(self)
        self._mother = []  # Non-None as uninitialized
        self._father = []  # Non-None as uninitialized

    @property
    def name(self):
        """:py:class:`Name` instance.
        """
        # +1 <<PERSONAL_NAME_STRUCTURE>> {0:M}
        return Name(self.sub_tags("NAME"), self.dialect)

    @property
    def sex(self):
        """Person sex, "M", "F", or "U"."""
        # +1 SEX <SEX_VALUE>
        sex_rec = self.sub_tag("SEX")
        if sex_rec:
            return sex_rec.value
        return "U"

    @property
    def mother(self):
        """Parent of this individual (:py:class:`Individual` or ``None``)"""
        if self._mother == []:
            self._mother = self.sub_tag("FAMC/WIFE")
        return self._mother

    @property
    def father(self):
        """Parent of this individual (:py:class:`Individual` or ``None``)"""
        if self._father == []:
            self._father = self.sub_tag("FAMC/HUSB")
        return self._father


# maps tag names to record class
_tag_class = dict(INDI=Individual,
                  NAME=NameRec,
                  DATE=Date)


def make_record(level, xref_id, tag, value, sub_records, offset, dialect,
                parser=None):
    """Create Record instance based on parameters.

    :param int level: Record level number.
    :param str xref_id: Record reference ID, possibly empty.
    :param str tag: Tag name.
    :param value: Record value, possibly empty. Value can be None, bytes, or
        string object, if it is bytes then it should be decoded into strings
        before calling freeze(), this is normally done by the parser which
        knows about encodings.
    :param list sub_records: Initial list of subordinate records,
        possibly empty. List can be updated later.
    :param int offset: Record location in a file.
    :param dialect: One of ``DIALECT_*`` constants.
    :param parser: Instance of :py:class:`~ged4py.parser.GedcomReader` class,
        only needed for records whose value is a pointer.
    :return: Instance of :py:class:`Record` (or one of its subclasses).

    This is the factory method for record instances, it can create different
    types of record based on tag of value:

        - if value has a pointer form (``@ref_id@``) then :py:class:`Pointer`
          instance is created
        - if tag is "INDI" then :py:class:`Individual` instance is created
        - if tag is "NAME" then :py:class:`NameRec` instance is created
        - if tag is "DATE" then :py:class:`Date` instance is created
        - otherwise  :py:class:`Record` instance is created

    Returned record is not complete, it could be updated by parser. When
    parser finishes updates it calls :py:meth:`Record.freeze` method to
    finalize record construction.
    """
    # value can be bytes or string so we check for both, 64 is code for '@'
    if value and len(value) > 2 and \
        ((value[0] == '@' and value[-1] == '@') or
         (value[0] == 64 and value[-1] == 64)):
        # this looks like a <pointer>, make a Pointer record
        klass = Pointer
        rec = klass(parser)
    else:
        klass = _tag_class.get(tag, Record)
        rec = klass()

    rec.level = level
    rec.xref_id = xref_id
    rec.tag = tag
    rec.value = value
    rec.sub_records = sub_records
    rec.offset = offset
    rec.dialect = dialect
    return rec
