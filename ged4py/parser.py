"""Module containing methods for parsing GEDCOM files.
"""


from __future__ import print_function, absolute_import, division

import codecs
import collections
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
gedcom_line = collections.namedtuple("gedcom_line", "level xref_id tag value")


class ParserError(Exception):
    """Class for exceptions raised for parsing errors.
    """
    pass


class CodecError(ParserError):
    """Class for exceptions raised for codec-related errors.
    """
    pass


def _get_codec(name):
    """Takes GEDCOM codec name and returns Python codec name
    """
    try:
        codec = codecs.lookup(name)
        return codec.name
    except LookupError:
        return None


def readlines(file, errors="strict"):
    """Generator method for lines in file.

    Iterates over lines in input file returning each line as a string.
    This method determines file encoding based on either BOM record or
    contents of the ``CHAR`` record.

    :param file: File or file-like object, must support `read()`,
        `readline()`, `tell()` and `seek()`. `read()` and `readline()`
        must return bytes (file must be open in binary mode)
    :param str errors: Controls error handling behavior during string
        decoding, accepts same values as standard `codecs.decode` method.
    :returns: Iterator for lines in file, string are decode and returned
        as UNICODE strings.
    :raises: :py:class:`CodecError` when codec name in file is unknown or
        when codec name in file contradicts codec determined from BOM.
    :raises: :py:class:`UnicodeDecodeError` when codec fails to decode
        input lines and `errors` is set to "strict" (default).
    """

    # try to determine initial codec
    ini_codec = check_bom(file)
    codec = ini_codec or 'ansel'

    update_codec = True

    while True:
        line = file.readline()
        if not line:
            break
        line = codecs.decode(line, codec, errors)
        line = line.lstrip().rstrip('\n')

        if update_codec:
            words = line.split()

            if len(words) >= 2 and words[0] == "0" and words[1] != "HEAD":
                # past header
                update_codec = False
            elif len(words) >= 3 and words[0] == "1" and words[1] == "CHAR":
                new_codec = _get_codec(words[2])
                if new_codec is None:
                    raise CodecError("Unknown codec name {0}".format(words[2]))
                if ini_codec is None:
                    codec = new_codec
                elif new_codec != ini_codec:
                    raise CodecError("CHAR codec {0} is different from BOM "
                                     "codec {1}".format(words[2], ini_codec))

        yield line


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

    :param input: Either file object or iterator over lines (e.g. one
        returned by :py:func:`readlines` method in this module).
    :param str errors: Controls error handling behavior during string
        decoding, accepts same values as standard `codecs.decode` method.
        This parameter is used only if `input` is a file object.
    :param str filename: Name of the file, it is only used for generating
        diagnostics.
    :returns: Iterator for gedcom_lines.
    :raises: :py:class:`ParserError` when lines have incorrect syntax.
    """

    if hasattr(input, "readline"):
        # has to wrap raw file into "readlines" to handle codecs
        input = readlines(input, errors)

    for lineno, line in enumerate(input, 1):

        match = _re_gedcom_line.match(line)
        if not match:
            raise ParserError("Invalid syntax at line "
                              "{0}:{1}".format(filename, lineno))

        yield gedcom_line(level=int(match.group('level')),
                          xref_id=match.group('xref'),
                          tag=match.group('tag'),
                          value=match.group('value'))
