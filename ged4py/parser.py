"""Module containing methods for parsing GEDCOM files.
"""


from __future__ import print_function, absolute_import, division

import codecs
import collections
import io
import re

from .detail.io import check_bom, guess_lineno

_re_gedcom_line = re.compile(r"""
        ^
        [ ]*(?P<level>\d+)                       # integer level number
        (?:[ ](?P<xref>@[A-Z-a-z0-9][^@]*@))?    # optional @xref@
        [ ](?P<tag>[A-Z-a-z0-9]+)                # tag name
        (?:[ ](?P<value>.*))?                    # optional value
        $
""", re.X)

# tuple class for gedcom_line grammar
gedcom_line = collections.namedtuple("gedcom_line",
                                     "level xref_id tag value offset")

# tuple class for gedcom_line grammar
gedcom_rec = collections.namedtuple("gedcom_rec",
                                    "level xref_id tag value "
                                    "sub_records offset")


class ParserError(Exception):
    """Class for exceptions raised for parsing errors.
    """
    pass


class CodecError(ParserError):
    """Class for exceptions raised for codec-related errors.
    """
    pass


def guess_codec(file, errors="strict"):
    """Look at file contents and guess its correct encoding.

    File must be open in binary mode and positioned at offset 0. If BOM
    record is present then it is assumed to be UTF-8 or UTF-16 encoded
    file. GEDCOM header is searched for CHAR record and encoding name
    is extracted from it, if BOM record is present then CHAR record
    must match BOM-defined encoding.

    :param file: File object, must be open in binary mode.
    :param str errors: Controls error handling behavior during string
        decoding, accepts same values as standard `codecs.decode` method.
    :returns: Name of the file codec.
    :raises: :py:class:`CodecError` when codec name in file is unknown or
        when codec name in file contradicts codec determined from BOM.
    :raises: :py:class:`UnicodeDecodeError` when codec fails to decode
        input lines and `errors` is set to "strict" (default).
    """

    # check BOM first
    bom_codec = check_bom(file)
    codec = bom_codec or 'ansel'

    # scan header until CHAR or end of header
    while True:

        line = file.readline()
        if not line:
            raise IOError("Unexpected EOF while reading GEDCOM header")

        line = codecs.decode(line, codec, errors)
        line = line.lstrip().rstrip('\n')

        words = line.split()

        if len(words) >= 2 and words[0] == "0" and words[1] != "HEAD":
            # past header but have not seen CHAR
            raise CodecError("GEDCOM header does not have CHAR record")
        elif len(words) >= 3 and words[0] == "1" and words[1] == "CHAR":
            try:
                new_codec = codecs.lookup(words[2]).name
            except LookupError:
                raise CodecError("Unknown codec name {0}".format(words[2]))
            if bom_codec is None:
                codec = new_codec
            elif new_codec != bom_codec:
                raise CodecError("CHAR codec {0} is different from BOM "
                                 "codec {1}".format(words[2], bom_codec))
            break

    # If BOM record is there and codec is utf-8 then use utf-8-sig to strip BOM
    if bom_codec == codecs.lookup('utf-8').name:
        codec = codecs.lookup('utf-8-sig').name

    return codec


def gedcom_open(filename, encoding=None, errors="strict"):
    """Open the file for reading in text mode.

    :param str filename: Name of the file to open.
    :param str encoding: If None (default) then file is analyzed using
        `guess_codec()` method to determine correct codec. Otherwise
        file is open using specified codec.
    :param str errors: Controls error handling behavior during string
        decoding, accepts same values as standard `codecs.decode` method.
    :returns: File object open in text mode with correct encoding set,
        this is likely to be a subclass of `io.TextIOBase`.
    :raises: :py:class:`CodecError` when codec name in file is unknown or
        when codec name in file contradicts codec determined from BOM.
    :raises: :py:class:`UnicodeDecodeError` when codec fails to decode
        input lines and `errors` is set to "strict" (default).
    """

    if encoding is None:
        with open(filename, 'rb') as gedfile:
            encoding = guess_codec(gedfile, errors=errors)

    return io.open(filename, 'rt', encoding=encoding, errors=errors)


def gedcom_lines(input, filename="<input>"):
    """Generator method for *gedcom lines*.

    GEDCOM line grammar is defined in Chapter 1 of GEDCOM standard, it
    consists if the level number, optional reference ID, tag name, and
    optional value separated by spaces. Chaper 1 is pure grammar level,
    it does not assign any semantics to tags or levels. Consequently
    this method does not perform any operations on the lines other than
    returning the lines in their order in file.

    This method iterates over all lines in input file and converts each
    line into :py:class:`gedcom_line` class.

    :param input: File object.
    :param str filename: Name of the file, it is only used for generating
        diagnostics.
    :returns: Iterator for gedcom_lines.
    :raises: :py:class:`ParserError` when lines have incorrect syntax.
    """

    while True:

        offset = input.tell()
        line = input.readline().rstrip('\n')
        if not line:
            break

        match = _re_gedcom_line.match(line)
        if not match:
            input.seek(offset)
            lineno = guess_lineno(input)
            raise ParserError("Invalid syntax at line "
                              "{0}({1}): `{2}'".format(filename, lineno, line))

        yield gedcom_line(level=int(match.group('level')),
                          xref_id=match.group('xref'),
                          tag=match.group('tag'),
                          value=match.group('value'),
                          offset=offset)


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


class GedcomReader(object):
    """Main interface for reading GEDCOM files
    """

    def __init__(self, fname, encoding=None, errors="strict"):
        self._fname = fname
        self._index0 = None   # list of level=0 record positions
        self._xref0 = None    # maps xref_id to level=0 record position

        # open the file
        self.file = gedcom_open(fname, encoding=encoding, errors=errors)

    @property
    def index0(self):
        if self._index0 is None:
            self._init_index()
        return self._index0

    @property
    def xref0(self):
        if self._xref0 is None:
            self._init_index()
        return self._xref0

    def _init_index(self):
        self._index0 = []
        self._xref0 = []
        # scan whole file for level=0 records
        self.file.seek(0)
        for gline in gedcom_lines(self.file, self._fname):
            if gline.level == 0:
                self._index0.append((gline.offset, gline.tag))
                if gline.xref_id:
                    self._xref0[gline.xref_id] = (gline.offset, gline.tag)

    def records0(self, tag=None):
        """Iterator over all level=0 records.
        """
        for offset, xtag in self.index0:
            if tag is None or tag == xtag:
                yield self.read_record(offset)

    def read_record(self, offset):
        """Read next complete record from a file starting at given position.

        Reads the record at given position and all its sub-records. Stops
        reading at EOF or next record with the same or higher (smaller) level
        number. File position after return from this method is not specified,
        re-position file if you want to read other records.

        Parameters
        ----------
        offset : int
            Position in file to start reading from.

        Returns
        -------
        `gedcom_rec` instance or None if offset points past EOF.

        Raises
        ------
        `ParserError` if `offsets` does not point to the beginning of a
        record or for any parsing errors.
        """
        stack = []  # stores per-level current records
        reclevel = None
        self.file.seek(offset)
        for gline in gedcom_lines(self.file, self._fname):
            level = gline.level
            if reclevel is None:
                # this is the first record, remember its level
                reclevel = level
            elif level <= reclevel:
                # stop at the record of the same or higher (smaller) level
                break
            # extend stack to fit this level
            stack.extend([None] * (level + 1 - len(stack)))

            rec = gedcom_rec(level=level, xref_id=gline.xref_id,
                             tag=gline.tag, value=gline.value,
                             sub_records=[], offset=gline.offset)

            # add to parent's sub-records list
            parent = stack[level - 1] if level > 0 else None
            if parent:
                parent.sub_records.append(rec)

            # store as current record at this level
            stack[level] = rec

        return stack[reclevel] if stack else None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.file.close()
