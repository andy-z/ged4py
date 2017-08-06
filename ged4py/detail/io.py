"""Internal module for I/O related methods.
"""

from __future__ import print_function, absolute_import, division

import codecs
import os


def check_bom(file):
    """Determines file codec from from its BOM record.

    If file starts with BOM record encoded with UTF-8 or UTF-16(BE/LE)
    then corresponding encoding name is returned, otherwise None is returned.
    In both cases file current position is set to after-BOM bytes. The file
    must be open in binary mode and positioned at offset 0.
    """

    # try to read first three bytes
    lead = file.read(3)
    if len(lead) == 3 and lead == codecs.BOM_UTF8:
        # UTF-8, position is already OK, use canonical name
        return codecs.lookup('utf-8').name
    elif len(lead) >= 2 and lead[:2] == codecs.BOM_UTF16_BE:
        # need to backup one character
        if len(lead) == 3:
            file.seek(-1, os.SEEK_CUR)
        return codecs.lookup('utf-16-be').name
    elif len(lead) >= 2 and lead[:2] == codecs.BOM_UTF16_LE:
        # need to backup one character
        if len(lead) == 3:
            file.seek(-1, os.SEEK_CUR)
        return codecs.lookup('utf-16-le').name
    else:
        # no BOM, rewind
        file.seek(-len(lead), os.SEEK_CUR)
        return None


def guess_lineno(file):
    """Guess current line number in a file.

    Guessing is done in a very crude way - scanning file from beginning
    until current offset and counting newlines. Only meant to be used in
    exceptional cases - generating line number for error message.
    """
    offset = file.tell()
    file.seek(0)
    startpos = 0
    lineno = 1
    # looks like file.read() return bytes in python3
    # so I need more complicated algorithm here
    while True:
        line = file.readline()
        if not line:
            break
        endpos = file.tell()
        if startpos <= offset < endpos:
            break
        lineno += 1
    file.seek(offset)
    return lineno
