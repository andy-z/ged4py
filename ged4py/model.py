# -*- coding: utf-8 -*-

"""Module containing Python in-memory model for GEDCOM data.
"""

from __future__ import print_function, absolute_import, division

__all__ = ['make_record', 'Record', 'Pointer', 'Name']

import re

from .detail.name import split_name

# Even though the structure of GEDCOM file is more or less fixed,
# interpretation of some data may vary depending on which application
# produced GEDCOM file. Constants define different known dialect which
# are handled by classes below.
DIALECT_DEFAULT = "DEF"
DIALECT_MYHERITAGE = "MYHER"  # myheritage.com
DIALECT_ALTREE = "AGELONG"  # Agelong Tree (genery.com)


class Record(object):
    """Class representing a parsed GEDCOM record in a generic format.

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
    :ivar int dialect: GEDCOM source dialect, one of the DIALECT_* values
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
        """
        pass

    def sub_tag(self, tag):
        """Returns direct sub-record with given tag name or None.
        """
        recs = [x for x in self.sub_records if x.tag == tag]
        return recs[0] if recs else None

    def sub_tags(self, tag):
        """Returns list of direct sub-records with given tag name.
        """
        return [x for x in self.sub_records if x.tag == tag]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        value = self.value
        if isinstance(value, (type(""), type(u""))) and len(value) > 32:
            value = value[:32] + "..."
        n_sub = len(self.sub_records)
        if self.xref_id:
            fmt = "{0}(level={1.level}, xref_id={1.xref_id}, tag={1.tag}, " \
                "value={2!r}, offset={1.offset}, #subrec={3})"
        else:
            fmt = "{0}(level={1.level}, tag={1.tag}, " \
                "value={2!r}, offset={1.offset}, #subrec={3})"
        return fmt.format(self.__class__.__name__, self, value, n_sub)


class Pointer(object):
    """Class representing a reference to a record in a GEDCOM file.

    This class wraps a GEDCOM pointer and adds few useful methods to locate
    and retrieve a pointed object. Instance of this class will be used in
    place of the GEDCOM pointers in the objects created by parser.

    :ivar str pointer: Value of the GEDCOM pointer (e.g. "@I1234@")
    """

    def __init__(self, pointer, registry):
        self.pointer = pointer
        self.registry = registry

    @property
    def object(self):
        """Retrieve pointed object.
        """
        return self.registry.get(self.pointer)

    def __str__(self):
        return "Pointer({0})".format(self.pointer)


class Name(Record):
    """Representation of the NAME record.

    This class adds few convenience methods for name manipulation. It also
    redefines the type of the `value` attribute, it's type is tuple.
    Value tuple can contain 3 or 4 elements, if there are 4 elements then
    last element is a maiden name. Second element of a tuple is surname,
    first and third elements are pieces of the given name (this is determined
    entirely by how name is represented in GEDCOM file). Any of the elements
    can be empty string. Few examples:

        ("John", "Smith", "")
        ("Mary Joan", "Smith", "", "Ivanova")    # maiden name
        ("", "Ivanov", "Ivan Ivanovich")
        ("John", "Smith", "Jr.")

    Client code usually does not need to create instances of this class
    directly, :py:meth:`make_record` should be used instead.
    """

    _surname_re = re.compile("(.*)\((.*)\)")

    def __init__(self):
        Record.__init__(self)
        self.name_tuple = None
        self.maiden = None

    def freeze(self):
        self.name_tuple = split_name(self.value)
        if self.dialect in [DIALECT_ALTREE]:
            # maiden name is part of surname (Surname (Maiden))
            match = self._surname_re.match(self.name_tuple[1])
            if match:
                surname = match.group(1).strip()
                self.name_tuple = (self.name_tuple[0],
                                   surname,
                                   self.name_tuple[2])
                self.maiden = match.group(2).strip()
        elif self.dialect in [DIALECT_MYHERITAGE]:
            # married name is in a special tag _MARNM
            surname = self.sub_tag("_MARNM")
            if surname:
                surname = surname.value
                self.maiden = self.name_tuple[1]
                self.name_tuple = (self.name_tuple[0],
                                   surname,
                                   self.name_tuple[2])
        self.value = self.name_tuple
        if self.maiden:
            self.value += (self.maiden,)

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


class Individual(Record):
    """Representation of the NAME record.

    This class adds few convenience methods for name manipulation.

    Client code usually does not need to create instances of this class
    directly, :py:meth:`make_record` should be used instead.
    """

    def __init__(self):
        Record.__init__(self)

    @property
    def names(self):
        """List of names (:py:class:`Name` instances).
        """
        # +1 <<PERSONAL_NAME_STRUCTURE>> {0:M}
        return self.sub_tags("NAME")


# maps tag names to record class
_tag_class = dict(INDI=Individual,
                  NAME=Name)


def make_record(level, xref_id, tag, value, sub_records, offset, dialect):
    """Create Record instance based on parameters.

    :param int level: Record level number.
    :param str xref_id: Record reference ID, possibly empty.
    :param str tag: Tag name.
    :param str value: Record value, possibly empty.
    :param list sub_records: Initial list of subordinate records,
        possibly empty. List can be updated later.
    :param int offset: Record location in a file.
    :param int dialect: One of DIALECT_* constants.
    :return: Instance of :py:class:`Record` (or one of its subclasses).
    """

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
