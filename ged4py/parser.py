"""Module containing methods for parsing GEDCOM files.
"""


from __future__ import print_function, absolute_import, division

try:
    import __builtin__ as builtins
except ImportError:
    import builtins
import codecs
import collections
import io
import itertools
import re

from .detail.io import check_bom

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

    # codec is OK now, re-open with correct codec
    # If BOM record is there and codec is utf-8 then use utf-8-sig to strip BOM
    if bom_codec == codecs.lookup('utf-8').name:
        codec = codecs.lookup('utf-8-sig').name

    return codec


def open(filename, encoding=None, errors="strict"):
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
        with builtins.open(filename, 'rb') as gedfile:
            encoding = guess_codec(gedfile, errors=errors)

    return io.open(filename, 'rt', encoding=encoding, errors=errors)


def gedcom_lines(input, errors="strict", filename="<input>"):
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
    :param str errors: Controls error handling behavior during string
        decoding, accepts same values as standard `codecs.decode` method.
        This parameter is used only if `input` is a file object.
    :param str filename: Name of the file, it is only used for generating
        diagnostics.
    :returns: Iterator for gedcom_lines.
    :raises: :py:class:`ParserError` when lines have incorrect syntax.
    """

    for lineno in itertools.count(1):

        offset = input.tell()
        line = input.readline()
        if not line:
            break

        match = _re_gedcom_line.match(line)
        if not match:
            raise ParserError("Invalid syntax at line "
                              "{0}:{1}".format(filename, lineno))

        yield gedcom_line(level=int(match.group('level')),
                          xref_id=match.group('xref'),
                          tag=match.group('tag'),
                          value=match.group('value'),
                          offset=offset)
