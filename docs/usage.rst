=====
Usage
=====

Currently :py:mod:`ged4py` supports parsing of existing GEDCOM files, there
is no support for (re-)generating GEDCOM data. The main interface for parsing
is :py:class:`ged4py.parser.GedcomReader` class. To create parser instance
one has to pass file with GEDCOM data as a single required parameter, this
can be either file name of a Python file object. If file object is passed
then the file has to be open in a binary mode and it has to support
``seek()`` and ``tell()`` methods. Example of instantiating a parser::

    from ged4py import GedcomReader

    path = "/path/to/file.gedcom"
    with GedcomReader(path) as parser:
        # GedcomReader provides context support
        ...

or using in-memory buffer as a file (could be useful for testing)::

    import io
    from ged4py import GedcomReader

    data = b"..."                 # make some binary date here
    with io.BytesIO(data) as file:
        parser = GedcomReader(file)
        ...

In most cases parser should be able to determine input file encoding from the
file if data in the file follows GEDCOM specification. In other cases parser
may need external help, if you know file encoding you can provide it as an
argument to parser::

    parser = GedcomReader(path, encoding="utf-8")

Any encoding supported by Python :py:mod:`codecs` module can be used as
argument, additionally this package defines ANSEL encoding, so "ansel" string
can be given as argument too.

By default parser raises exception if it encounters errors while decoding
data in a file. To override this behavior one can specify different error
policy, following the same pattern as standard :py:func:`codecs.decode`
method, e.g.::

    parser = GedcomReader(path, encoding="utf-8", errors='replace')

Main mode of operation for parser is iterating over records in a file in
sequential manner. GEDCOM records are organized in hierarchical structures,
and ged4py parser facilitates access to these hierarchies by grouping
records in tree-like structures. Instead providing iterator over every
record in a file parser iterates over top-level (level 0) records, and
for each level-0 record it returns nested structure consisting of the
records below level 0.

The main method of the parser is the method
:py:meth:`~ged4py.parser.GedcomReader.records0` which returns iterator over all
level-0 records. Method takes an optional argument for a tag name, without
argument all level-0 records are returned by iterator (starting with "HEAD"
and ending with "TRLR"). If tag is given then only the records with
corresponding tag are returned::

    with GedcomReader(path) as parser:
        # iterate over all INDI records
        for record in parser.records0("INDI"):
            ....

Records returned by iterator are instances of class
:py:class:`ged4py.model.Record` or one of its few sub-classes. Each record
instance has a small set of attributes:

- ``level`` - record level, 0 for top-level records
- ``xref_id`` - record reference ID, may be ``None``
- ``tag`` - record tag name
- ``value`` - record value, can be `None`, string, or value of some other
  type depending on record type
- ``sub_records`` - list of subordinate records, direct sub-records of this
  record, it is easier to access items in this list using methods described
  below.

:py:class:`~ged4py.model.Record` class has few convenience methods:

- :py:meth:`~ged4py.model.Record.sub_tags` - return all direct subordinate
  records with a given tag name, list of records is returned, possibly empty.
- :py:meth:`~ged4py.model.Record.sub_tag` - return subordinate record with a
  given tag name (or tag "path"), if there is more than one record with
  matching tag then first one is returned, without match ``None`` is returned.
- :py:meth:`~ged4py.model.Record.sub_tag_value` - return value of subordinate
  record with a given tag name (or tag "path"), or ``None`` if record is not
  found or its value is ``None``.

There are few specialized sub-classes of :py:class:`~ged4py.model.Record`
each corresponding to specific record tag:

- NAME records generate :py:class:`ged4py.model.NameRec` instances, this
  class knows how to split name representation into name components (first,
  last, maiden) and has attributes for accessing those.
- DATE records generate :py:class:`ged4py.model.Date` instances, the
  ``value`` attribute of this class is converted into
  :py:class:`ged4py.detail.date.DateValue` instance.
- INDI records are represented by :py:class:`ged4py.model.Individual` class.
- "pointer" records whose ``value`` has special GEDCOM <POINTER> syntax
  (``@xref_id@``) are represented by :py:class:`ged4py.model.Pointer`
  class. This class has special property ``ref`` which returns referenced
  record. Methods :py:meth:`~ged4py.model.Record.sub_tag` and
  :py:meth:`~ged4py.model.Record.sub_tag_value` have keyword argument
  ``follow`` which can be set to ``True`` to allow automatic dereferencing
  of the pointer records.
