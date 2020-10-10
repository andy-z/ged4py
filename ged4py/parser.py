"""Module containing methods for parsing GEDCOM files.
"""

__all__ = ['GedcomReader', 'ParserError', 'CodecError', 'IntegrityError',
           'guess_codec', 'GedcomLine']

import codecs
import io
import logging
import re
from typing import NamedTuple

from .detail.io import check_bom, guess_lineno, BinaryFileCR
from . import model

_log = logging.getLogger(__name__)

# records are bytes, regex is for bytes too
_re_GedcomLine = re.compile(br"""
        ^
        [ ]*(?P<level>\d+)                       # integer level number
        (?:[ ]*(?P<xref>@[A-Z-a-z0-9][^@]*@))?    # optional @xref@
        [ ]*(?P<tag>[A-Z-a-z0-9_]+)               # tag name
        (?:[ ](?P<value>.*))?                    # optional value
        $
""", re.X)


class GedcomLine(NamedTuple):
    """Class representing single line in a GEDCOM file.

    .. note::

        Mostly for internal use by parser, most clients do not need to know
        about this class.

    Attributes
    ----------
    level : `int`
    xref_id : `str`, possibly empty or ``None``
    tag : `str`, required, non-empty
    value : `bytes`, possibly empty or ``None``
    offset : `int`
    """
    level: int
    """Record level number (`int`)"""

    xref_id: str
    """Reference for this record (`str` or ``None``)"""

    tag: str
    """Tag name (`str`)"""

    value: bytes
    """Record value (`bytes`)"""

    offset: int
    """Record offset in a file (`int`)"""


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

    Parameters
    ----------
    file
        File object, must be open in binary mode.
    errors : `str`, optional
        Controls error handling behavior during string decoding, accepts same
        values as standard `codecs.decode` method.
    require_char : `bool`, optional
        If ``True`` then exception is thrown if CHAR record is not found in a
        header, if False and CHAR is not in the header then codec determined
        from BOM or "gedcom" is returned.
    warn : `bool`, optional
        If True (default) then generate error/warning messages for illegal
        encodings.

    Returns
    -------
    codec_name : `str`
        The name of the codec in this file.
    bom_size : `int`
        Size of the BOM record, 0 if no BOM record.

    Raises
    ------
    CodecError
        Raised if codec name in file is unknown or when codec name in file
        contradicts codec determined from BOM.
    UnicodeDecodeError
        Raised if codec fails to decode input lines and `errors` is set to
        "strict" (default).
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


class GedcomReader:
    """Main interface for reading GEDCOM files.

    Parameters
    ----------
    file
        File name or file object open in binary mode, file must be seekable.
    encoding : `str`, optional
        If ``None`` (default) then file is analyzed using `guess_codec()`
        method to determine correct codec. Otherwise file is open using
        specified codec.
    errors : `str`, optional
        Controls error handling behavior during string decoding, accepts same
        values as standard `codecs.decode` method.
    require_char : `bool`, optional
        If True then exception is thrown if CHAR record is not found in a
        header, if False and CHAR is not in the header then codec determined
        from BOM or "gedcom" is used.

    Notes
    -----
    Instance of this class is used to read and parse single GEDCOM file.
    Records in GEDCOM file are transformed into instances of types defined in
    `ged4py.model` module, either `ged4py.model.Record` class or one of its
    sub-classes. Main method of access to the data in the file is by iterating
    over level-0 records, optionally restricted by the tag name. The method
    which does this is `GedcomReader.records0()`. Most commonly the code which
    reads GEDCOM file at the top-level loop will look like this::

        with GedcomReader(path) as parser:
            # iterate over each INDI record in a file
            for record in parser.records0("INDI"):
                # do something with the record or navigate to other linked records

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
        """List of level=0 record positions and tag names (`list[(int, str)]`).
        """
        if self._index0 is None:
            self._init_index()
        return self._index0

    @property
    def xref0(self):
        """Dictionary which maps xref_id to level=0 record position and
        tag name (`dict[str, (int, str)]`).
        """
        if self._xref0 is None:
            self._init_index()
        return self._xref0

    @property
    def header(self):
        """Header record (`ged4py.model.Record`).
        """
        if self._index0 is None:
            self._init_index()
        return self._header

    def _init_index(self):
        _log.debug("in _init_index")
        self._index0 = []
        self._xref0 = {}
        # scan whole file for level=0 records
        for gline in self.GedcomLines(self._bom_size):
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
        """File dialect as one of `ged4py.model.Dialect` enums.
        """
        if self._dialect is None:
            self._dialect = model.Dialect.DEFAULT
            if self.header:
                source = self.header.sub_tag("SOUR")
                if source:
                    if source.value == "MYHERITAGE":
                        self._dialect = model.Dialect.MYHERITAGE
                    elif source.value in ("ALTREE", "AgelongTree"):
                        self._dialect = model.Dialect.ALTREE
                    elif source.value == "ANCESTRIS":
                        self._dialect = model.Dialect.ANCESTRIS
        return self._dialect

    @dialect.setter
    def dialect(self, value):
        self._dialect = value

    def GedcomLines(self, offset):
        """Generator method for *gedcom lines*.

        Parameters
        ----------
        offset : `int`
            Position in the file to start reading.

        Yields
        ------
        line : `GedcomLine`
            An object representing one line of GEDCOM file.

        Raises
        ------
        ParserError
            Raised if lines have incorrect syntax.

        Notes
        -----
        GEDCOM line grammar is defined in Chapter 1 of GEDCOM standard, it
        consists of the level number, optional reference ID, tag name, and
        optional value separated by spaces. Chaper 1 is pure grammar level,
        it does not assign any semantics to tags or levels. Consequently
        this method does not perform any operations on the lines other than
        returning the lines in their order in file.

        This method iterates over all lines in input file and converts each
        line into `GedcomLine` class. It is an implementation detail used by
        other methods, most clients will not need to use this method.
        """

        self._file.seek(offset)

        prev_gline = None
        while True:

            offset = self._file.tell()
            line = self._file.readline()  # stops at \n
            if not line:
                break
            line = line.lstrip().rstrip(b"\r\n")

            match = _re_GedcomLine.match(line)
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

            gline = GedcomLine(level=level,
                               xref_id=xref_id,
                               tag=tag,
                               value=match.group('value'),
                               offset=offset)
            yield gline

            prev_gline = gline

    def records0(self, tag=None):
        """Iterator over level=0 records with given tag.

        This is the main method of this class. Clients access data in GEDCOM
        files by iterating over level=0 records and then navigating to
        sub-records using the methods of the `~ged4py.model.Record` class.

        Parameters
        ----------
        tag : `str`, optional
            If tag is ``None`` (default) then return all level=0 records,
            otherwise return level=0 records with the given tag.

        Yields
        ------
        record : `~ged4py.model.Record`
            Instances of `~ged4py.model.Record` or its subclasses.
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

        This is mostly for internal use, regular clients don't need to use it.

        Parameters
        ----------
        offset : `int`
            Position in the file to start reading.

        Returns
        -------
        record : `~ged4py.model.Record` or ``None``
            `model.Record` instance or None if offset points past EOF.

        Raises
        ------
        ParserError
            Raised if `offsets` does not point to the beginning of a record or
            for any parsing errors.
        """
        _log.debug("in read_record(%s)", offset)
        stack = []  # stores per-level current records
        reclevel = None
        for gline in self.GedcomLines(offset):
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
        parent : `ged4py.model.Record`
            Parent record of the new record
        gline : `GedcomLine`
            Current parsed line

        Returns
        -------
        record : `ged4py.model.Record` or None
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
        dialect = model.Dialect.DEFAULT
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
