# -*- coding: utf-8 -*-

"""Module containing Python in-memory model for GEDCOM data.
"""

from __future__ import print_function, absolute_import, division

__all__ = ['make_record', 'Record', 'Pointer', 'Name']


class Record(object):
    """Class representing a parsed GEDCOM record in a generic format.

    Client code usually does not need to create instances of this class
    directly, :py:meth:`make_record` should be used instead. If you create
    an instance of this class (or its subclass then you are responsible for
    filling its attributes.

    :ivar int level: Record level number
    :ivar str xref_id: Record reference ID, possibly empty.
    :ivar str tag: Tag name
    :ivar str value: Record value, possibly empty
    :ivar list sub_records: List of subordinate records, possibly empty
    :ivar int offset: Record location in a file
    """
    def __init__(self):
        self.level = None
        self.xref_id = None
        self.tag = None
        self.value = None
        self.sub_records = None
        self.offset = None

    def sub_tags(self, tag):
        """Returns list of direct sub-records with given tag name
        """
        return [x for x in self.sub_records if x.tag == tag]

    def __str__(self):
        value = self.value
        if value and len(value) > 32:
            value = value[:32]
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

    Attributes
    ----------
    pointer : str
        Value of the GEDCOM pointer (e.g. "@I1234@")
    object : object
        Pointed object
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

    This class adds few convenience methods for name manipulation.

    Client code usually does not need to create instances of this class
    directly, :py:method:`make_record` should be used instead.
    """

    def __init__(self):
        Record.__init__(self)


_tag_class = dict(NAME=Name)


def make_record(level, xref_id, tag, value, sub_records, offset):
    """Create Record instance based on parameters.

    :param int level: Record level number.
    :param str xref_id: Record reference ID, possibly empty.
    :param str tag: Tag name.
    :param str value: Record value, possibly empty.
    :param list sub_records: Initial list of subordinate records,
        possibly empty. List can be updated later.
    :param int offset: Record location in a file.
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
    return rec
