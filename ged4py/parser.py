"""Module containing methods for parsing GEDCOM files.
"""


from __future__ import print_function, absolute_import, division

__all__ = ['GedcomReader', 'ParserError', 'CodecError', 'IntegrityError',
           'guess_codec']

import codecs
import collections
import io
import logging
import re

from .detail.io import check_bom, guess_lineno, BinaryFileCR
from . import model

_log = logging.getLogger(__name__)

# records are bytes, regex is for bytes too
_re_gedcom_line = re.compile(br"""
        ^
        [ ]*(?P<level>\d+)                       # integer level number
        (?:[ ]*(?P<xref>@[A-Z-a-z0-9][^@]*@))?    # optional @xref@
        [ ]*(?P<tag>[A-Z-a-z0-9_]+)               # tag name
        (?:[ ](?P<value>.*))?                    # optional value
        $
""", re.X)

# tuple class for gedcom_line grammar:
#   level: int
#   xref_id: str, possibly empty or None
#   tag: str, required, non-empty
#   value: bytes, possibly empty or None
#   offset: int
gedcom_line = collections.namedtuple("gedcom_line",
                                     "level xref_id tag value offset")


class ParserError(Exception):
    """Class for exceptions raised for parsing errors.
    """
    pass


class IntegrityError(Exception):
    """Class for exceptions raised for structural errors, e.g. when record
    level nesting is inconsistent.
    """
    pass


class CodecError(ParserError):
    """Class for exceptions raised for codec-related errors.
    """
    pass


def guess_codec(file, errors="strict", require_char=False, warn=True):
    """Look at file contents and guess its correct encoding.

    File must be open in binary mode and positioned at offset 0. If BOM
    record is present then it is assumed to be UTF-8 or UTF-16 encoded
    file. GEDCOM header is searched for CHAR record and encoding name
    is extracted from it, if BOM record is present then CHAR record
    must match BOM-defined encoding.

    :param file: File object, must be open in binary mode.
    :param str errors: Controls error handling behavior during string
        decoding, accepts same values as standard `codecs.decode` method.
    :param bool require_char: If True then exception is thrown if CHAR
        record is not found in a header, if False and CHAR is not in the
        header then codec determined from BOM or "gedcom" is returned.
    :param bool warn: If True (default) then generate error/warning messages
        for illegal encodings.
    :returns: Tuple (codec_name, bom_size)
    :raises: :py:class:`CodecError` when codec name in file is unknown or
        when codec name in file contradicts codec determined from BOM.
    :raises: :py:class:`UnicodeDecodeError` when codec fails to decode
        input lines and `errors` is set to "strict" (default).
    """

    # set of illegal but unambiguous encodings and their corresponding codecs
    illegal_encodings = {
        "windows-1250": "cp1250",
        "windows-1251": "cp1251",
        "cp1252": "cp1252",
        "iso-8859-1": "iso8859-1",
        "iso8859-1": "iso8859-1",
    }
    # set of ambiguous (and illegal) encodings
    ambiguous_encodings = {
        'ibmpc': 'cp437',
        "ibm": "cp437",
        "ibm-pc": "cp437",
        "oem": "cp437",
        "msdos": "cp850",
        "ibm dos": "cp850",
        "ms-dos": "cp850",
        "ansi": "cp1252",
        "windows": "cp1252",
        "ibm_windows": "cp1252",
        "ibm windows": "cp1252",
        "iso8859": "iso8859-1",
        "latin1": "iso8859-1",
        "macintosh": "mac-roman",
    }
    illegal_encodings.update(ambiguous_encodings)
    # full set of encodings, including legal ones
    gedcom_char_to_codec = {"ansel": "gedcom"}
    gedcom_char_to_codec.update(illegal_encodings)

    # check BOM first
    bom_codec = check_bom(file)
    bom_size = file.tell()
    codec = bom_codec or 'gedcom'

    # scan header until CHAR or end of header
    lineno = 0
    while True:

        lineno += 1

        # this stops at '\n'
        line = file.readline()
        if not line:
            raise IOError("Unexpected EOF while reading GEDCOM header")

        # do not decode bytes to strings here, reason is that some
        # stupid apps split CONC record at byte level (in middle of
        # of multi-byte characters). This implies that we can only
        # work with encodings that have ASCII as single-byte subset.

        line = line.lstrip().rstrip(b"\r\n")
        words = line.split()

        if len(words) >= 2 and words[0] == b"0" and words[1] != b"HEAD":
            # past header but have not seen CHAR
            if require_char:
                raise CodecError("GEDCOM header does not have CHAR record")
            else:
                break
        elif len(words) >= 3 and words[0] == b"1" and words[1] == b"CHAR":
            try:
                enc = b" ".join(words[2:]).decode(codec, errors)
                encoding = gedcom_char_to_codec.get(enc.lower(), enc.lower())
                if enc.lower() in illegal_encodings and warn:
                    _log.error("Line %d: \"%s\" - \"%s\" is not a legal "
                               "character set or encoding.", lineno, line, enc)
                    if enc.lower() in ambiguous_encodings:
                        _log.warning("Character set (\"%s\") is ambiguous, it "
                                     "will be interpreted as \"%s\"",
                                     enc, encoding)
                new_codec = codecs.lookup(encoding).name
            except LookupError:
                raise CodecError("Unknown codec name '{0}'".format(enc))
            if bom_codec is None:
                codec = new_codec
            elif new_codec != bom_codec:
                raise CodecError("CHAR codec {0} is different from BOM "
                                 "codec {1}".format(new_codec, bom_codec))
            break

    return codec, bom_size


class GedcomReader(object):
    """Main interface for reading GEDCOM files.

    :param file: File name or file object open in binary mode, file must
        be seekable.
    :param str encoding: If None (default) then file is analyzed using
        `guess_codec()` method to determine correct codec. Otherwise
        file is open using specified codec.
    :param str errors: Controls error handling behavior during string
        decoding, accepts same values as standard `codecs.decode` method.
    :param bool require_char: If True then exception is thrown if CHAR
        record is not found in a header, if False and CHAR is not in the
        header then codec determined from BOM or "gedcom" is used.
    """

    def __init__(self, file, encoding=None, errors="strict",
                 require_char=False):
        self._encoding = encoding
        self._errors = errors
        self._bom_size = 0
        self._index0 = None   # list of level=0 record positions
        self._xref0 = None    # maps xref_id to level=0 record position
        self._header = None
        self._dialect = None

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
        self._file = BinaryFileCR(self._file)

        # check codec and BOM
        try:
            encoding, self._bom_size = guess_codec(self._file,
                                                   errors=self._errors,
                                                   require_char=require_char,
                                                   warn=self._encoding is None)
        except Exception:
            self._file.close()
            raise
        self._file.seek(self._bom_size)
        if not self._encoding:
            self._encoding = encoding

    @property
    def index0(self):
        """List of level=0 record positions and tag names.
        """
        if self._index0 is None:
            self._init_index()
        return self._index0

    @property
    def xref0(self):
        """Dictionary which maps xref_id to level=0 record position and
        tag name.
        """
        if self._xref0 is None:
            self._init_index()
        return self._xref0

    @property
    def header(self):
        """Header record.
        """
        if self._index0 is None:
            self._init_index()
        return self._header

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
        if self._index0 and self._index0[0][1] == 'HEAD':
            self._header = self.read_record(self._index0[0][0])
        _log.debug("_init_index done")

    @property
    def dialect(self):
        """File dialect as one of model.DIALECT_* constants
        """
        if self._dialect is None:
            self._dialect = model.DIALECT_DEFAULT
            if self.header:
                source = self.header.sub_tag("SOUR")
                if source:
                    if source.value == "MYHERITAGE":
                        self._dialect = model.DIALECT_MYHERITAGE
                    elif source.value == "ALTREE":
                        self._dialect = model.DIALECT_ALTREE
                    elif source.value == "ANCESTRIS":
                        self._dialect = model.DIALECT_ANCESTRIS
        return self._dialect

    @dialect.setter
    def dialect(self, value):
        self._dialect = value

    def gedcom_lines(self, offset):
        """Generator method for *gedcom lines*.

        GEDCOM line grammar is defined in Chapter 1 of GEDCOM standard, it
        consists of the level number, optional reference ID, tag name, and
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

        prev_gline = None
        while True:

            offset = self._file.tell()
            line = self._file.readline()  # stops at \n
            if not line:
                break
            line = line.lstrip().rstrip(b"\r\n")

            match = _re_gedcom_line.match(line)
            if not match:
                self._file.seek(offset)
                lineno = guess_lineno(self._file)
                line = line.decode(self._encoding, "ignore")
                raise ParserError("Invalid syntax at line "
                                  "{0}: `{1}'".format(lineno, line))

            level = int(match.group('level'))
            xref_id = match.group('xref')
            if xref_id:
                xref_id = xref_id.decode(self._encoding, self._errors)
            tag = match.group('tag').decode(self._encoding, self._errors)

            # simple structural integrity check
            if prev_gline is not None:
                if level - prev_gline.level > 1:
                    # nested levels should be incremental (+1)
                    self._file.seek(offset)
                    lineno = guess_lineno(self._file)
                    line = line.decode(self._encoding, "ignore")
                    raise IntegrityError("Structural integrity - "
                                         "illegal level nesting at line "
                                         "{0}: `{1}'".format(lineno, line))
                if tag in ("CONT", "CONC"):
                    # CONT/CONC level must be +1 from preceding non-CONT/CONC
                    # record or the same as preceding CONT/CONC record
                    if ((prev_gline.tag in ("CONT", "CONC") and
                         level != prev_gline.level) or
                        (prev_gline.tag not in ("CONT", "CONC") and
                         level - prev_gline.level != 1)):
                        self._file.seek(offset)
                        lineno = guess_lineno(self._file)
                        line = line.decode(self._encoding, "ignore")
                        raise IntegrityError("Structural integrity -  illegal "
                                             "CONC/CONT nesting at line "
                                             "{0}: `{1}'".format(lineno, line))

            gline = gedcom_line(level=level,
                                xref_id=xref_id,
                                tag=tag,
                                value=match.group('value'),
                                offset=offset)
            yield gline

            prev_gline = gline

    def records0(self, tag=None):
        """Iterator over all level=0 records.

        :param str tag: If ``None`` is given (default) then return all level=0
            records, otherwise return level=0 records with the given tag.
        """
        _log.debug("in records0")
        for offset, xtag in self.index0:
            _log.debug("    records0: offset: %s; xtag: %s", offset, xtag)
            if tag is None or tag == xtag:
                yield self.read_record(offset)

    def read_record(self, offset):
        """Read next complete record from a file starting at given position.

        Reads the record at given position and all its sub-records. Stops
        reading at EOF or next record with the same or higher (smaller) level
        number. File position after return from this method is not specified,
        re-position file if you want to read other records.

        :param int offset: Position in file to start reading from.
        :return: :py:class:`model.Record` instance or None if offset points
            past EOF.
        :raises: :py:exc:`ParserError` if `offsets` does not point to the
            beginning of a record or for any parsing errors.
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

            # All previously seen records at this level and below can
            # be finalized now
            for rec in reversed(stack[level:]):
                # decode bytes value into string
                if rec:
                    if rec.value is not None:
                        rec.value = rec.value.decode(self._encoding,
                                                     self._errors)
                    rec.freeze()
#                    _log.debug("    read_record, rec: %s", rec)
            del stack[level + 1:]

            # extend stack to fit this level (and make parent levels if needed)
            stack.extend([None] * (level + 1 - len(stack)))

            # make Record out of it (it can be updated later)
            parent = stack[level - 1] if level > 0 else None
            rec = self._make_record(parent, gline)

            # store as current record at this level
            stack[level] = rec

        for rec in reversed(stack[reclevel:]):
            if rec:
                if rec.value is not None:
                    rec.value = rec.value.decode(self._encoding, self._errors)
                rec.freeze()
                _log.debug("    read_record, rec: %s", rec)

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
        parent : `model.Record`
            Parent record of the new record
        gline : `gedcom_line`
            Current parsed line

        Returns
        -------
        `model.Record` or None
        """

        if parent and gline.tag in ("CONT", "CONC"):
            # concatenate, only for non-BLOBs
            if parent.tag != "BLOB":
                # have to be careful concatenating empty/None values
                value = gline.value
                if gline.tag == "CONT":
                    value = b"\n" + (value or b"")
                if value is not None:
                    parent.value = (parent.value or b"") + value
            return None

        # avoid infinite cycle
        dialect = model.DIALECT_DEFAULT
        if not (gline.level == 0 and gline.tag == "HEAD") and self._header:
            dialect = self.dialect
        rec = model.make_record(level=gline.level, xref_id=gline.xref_id,
                                tag=gline.tag, value=gline.value,
                                sub_records=[], offset=gline.offset,
                                dialect=dialect, parser=self)

        # add to parent's sub-records list
        if parent:
            parent.sub_records.append(rec)

        return rec

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._file.close()
