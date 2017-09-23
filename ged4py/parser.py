"""Module containing methods for parsing GEDCOM files.
"""


from __future__ import print_function, absolute_import, division

import codecs
import collections
import io
import logging
import re

from .detail.io import check_bom, guess_lineno

_log = logging.getLogger(__name__)

_re_gedcom_line = re.compile(r"""
        ^
        [ ]*(?P<level>\d+)                       # integer level number
        (?:[ ](?P<xref>@[A-Z-a-z0-9][^@]*@))?    # optional @xref@
        [ ](?P<tag>[A-Z-a-z0-9_]+)               # tag name
        (?:[ ](?P<value>.*))?                    # optional value
        $
""", re.X)

# tuple class for gedcom_line grammar
gedcom_line = collections.namedtuple("gedcom_line",
                                     "level xref_id tag value offset")


class gedcom_rec(object):
    """Class representing a parsed GEDCOM record.

    Attributes
    ----------
    level : int
        Record level number
    xref_id : str
        Record reference ID, possibly empty.
    tag : str
        Tag name
    value : str
        Record value, possibly empty
    sub_records : list
        List of subordinate records, possibly empty
    offset : int
        Record location in a file
    """
    def __init__(self, level, xref_id, tag, value, sub_records, offset):
        self.level = level
        self.xref_id = xref_id
        self.tag = tag
        self.value = value
        self.sub_records = sub_records
        self.offset = offset


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
    :returns: Tuple (codec_name, bom_size)
    :raises: :py:class:`CodecError` when codec name in file is unknown or
        when codec name in file contradicts codec determined from BOM.
    :raises: :py:class:`UnicodeDecodeError` when codec fails to decode
        input lines and `errors` is set to "strict" (default).
    """

    # check BOM first
    bom_codec = check_bom(file)
    bom_size = file.tell()
    codec = bom_codec or 'ansel'

    # scan header until CHAR or end of header
    while True:

        line = file.readline()
        if not line:
            raise IOError("Unexpected EOF while reading GEDCOM header")

        line = codecs.decode(line, codec, errors)
        line = line.lstrip().rstrip('\r\n')

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

    return codec, bom_size


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
    """Main interface for reading GEDCOM files.

    :param str file: File name or file object open in binary mode, file must
        be seekable.
    :param str encoding: If None (default) then file is analyzed using
        `guess_codec()` method to determine correct codec. Otherwise
        file is open using specified codec.
    :param str errors: Controls error handling behavior during string
        decoding, accepts same values as standard `codecs.decode` method.
    """

    def __init__(self, file, encoding=None, errors="strict"):
        self._encoding = encoding
        self._errors = errors
        self._bom_size = 0
        self._index0 = None   # list of level=0 record positions
        self._xref0 = None    # maps xref_id to level=0 record position

        # open the file
        if hasattr(file, 'read'):
            # assume it is a file already
            if hasattr(file, 'seekable'):
                # check that it supports seek()
                if not file.seekable():
                    raise IOError("Input file does not support seek.")
            self._file = file
        else:
            raw = io.FileIO(file)
            self._file = io.BufferedReader(raw)

        # check codec and BOM
        encoding, self._bom_size = guess_codec(self._file, errors=self._errors)
        self._file.seek(self._bom_size)
        if not self._encoding:
            self._encoding = encoding

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
        _log.debug("in _init_index")
        self._index0 = []
        self._xref0 = {}
        # scan whole file for level=0 records
        for gline in self.gedcom_lines(self._bom_size):
            _log.debug("  _init_index gline: %s", gline)
            if gline.level == 0:
                self._index0.append((gline.offset, gline.tag))
                if gline.xref_id:
                    self._xref0[gline.xref_id] = (gline.offset, gline.tag)
            _log.debug("  _init_index gline: done proc")
        _log.debug("_init_index done")

    def gedcom_lines(self, offset):
        """Generator method for *gedcom lines*.

        GEDCOM line grammar is defined in Chapter 1 of GEDCOM standard, it
        consists if the level number, optional reference ID, tag name, and
        optional value separated by spaces. Chaper 1 is pure grammar level,
        it does not assign any semantics to tags or levels. Consequently
        this method does not perform any operations on the lines other than
        returning the lines in their order in file.

        This method iterates over all lines in input file and converts each
        line into :py:class:`gedcom_line` class.

        :param int offset: Position in the file to start reading.
        :returns: Iterator for gedcom_lines.
        :raises: :py:class:`ParserError` when lines have incorrect syntax.
        """

        self._file.seek(offset)

        while True:

            offset = self._file.tell()
            line = self._file.readline()
            if not line:
                break
            line = line.decode(self._encoding, self._errors)
            line = line.rstrip('\r\n')

            match = _re_gedcom_line.match(line)
            if not match:
                self._file.seek(offset)
                lineno = guess_lineno(self._file)
                raise ParserError("Invalid syntax at line "
                                  "{0}: `{1}'".format(lineno, line))

            yield gedcom_line(level=int(match.group('level')),
                              xref_id=match.group('xref'),
                              tag=match.group('tag'),
                              value=match.group('value'),
                              offset=offset)

    def records0(self, tag=None):
        """Iterator over all level=0 records.
        """
        _log.debug("in records0")
        for offset, xtag in self.index0:
            _log.debug("offset, xtag: %s, %s", offset, xtag)
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
        _log.debug("in read_record(%s)", offset)
        stack = []  # stores per-level current records
        reclevel = None
        for gline in self.gedcom_lines(offset):
            _log.debug("    read_record, gline: %s", gline)
            level = gline.level
            if reclevel is None:
                # this is the first record, remember its level
                reclevel = level
            elif level <= reclevel:
                # stop at the record of the same or higher (smaller) level
                break

            # extend stack to fit this level (and make parent levels if needed)
            stack.extend([None] * (level + 1 - len(stack)))

            parent = stack[level - 1] if level > 0 else None
            rec = self._make_record(parent, gline)

            # store as current record at this level
            if rec:
                stack[level] = rec

        return stack[reclevel] if stack else None

    def _make_record(self, parent, gline):
        """Process next record.

        This method created new record from the line read from file if
        needed and/or updates its parent record. If the parent record tag
        is ``BLOB`` and new record tag is ``CONT`` then record is skipped
        entirely and None is returned. Otherwise if new record tag is ``CONT``
        or ``CONC`` its value is added to parent value. For all other tags
        new record is made and it is added to parent sub_records attribute.

        Parameters
        ----------
        parent : `gedcom_rec`
            Parent record of the new record
        gline : `gedcom_line`
            Current parsed line

        Returns
        -------
        `gedcom_rec` or None,
        """

        if parent and gline.tag in ("CONT", "CONC"):
            # concatenate, only for non-BLOBs
            if parent.tag != "BLOB":
                # have to be careful concatenating empty/None values
                value = gline.value
                if gline.tag == "CONT":
                    value = "\n" + (value or "")
                if value is not None:
                    parent.value = (parent.value or "") + value
            return None

        rec = gedcom_rec(level=gline.level, xref_id=gline.xref_id,
                         tag=gline.tag, value=gline.value,
                         sub_records=[], offset=gline.offset)

        # add to parent's sub-records list
        if parent:
            parent.sub_records.append(rec)

        return rec

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._file.close()
