"""Module containing methods for parsing GEDCOM files.
"""


from __future__ import print_function, absolute_import, division

import codecs
import os


class ParserError(Exception):
    pass


class CodecError(ParserError):
    pass


def _guess_initial_codec(file):
    """Determines initial codec to use for parsing.

    If file starts with BOM record encoded with UTF-8 or UTF-16(BE/LE)
    then corresponding encoding name is returned, otherwise None is returned.
    In both cases file current position is set to after-BOM bytes. The file
    must be open in binary mode.
    """

    # try to read first three bytes
    lead = file.read(3)
    if len(lead) == 3 and lead == codecs.BOM_UTF8:
        # UTF-8, position is already OK, use canonical name
        return codecs.lookup('utf-8').name
    elif len(lead) >= 2 and lead[:2] == codecs.BOM_UTF16_BE:
        # need to backup one character
        file.seek(-1, os.SEEK_CUR)
        return codecs.lookup('utf_16_be').name
    elif len(lead) >= 2 and lead[:2] == codecs.BOM_UTF16_LE:
        # need to backup one character
        file.seek(-1, os.SEEK_CUR)
        return codecs.lookup('utf_16_le').name
    else:
        # no BOM, rewind
        file.seek(-3, os.SEEK_CUR)
        return None


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
    """

    # try to determine initial codec
    ini_codec = _guess_initial_codec(file)
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
