"""Internal module for I/O related methods."""

import codecs
import io
import os
from typing import BinaryIO


def check_bom(file: io.IOBase) -> str | None:
    """Determine file codec from from its BOM record.

    If file starts with BOM record encoded with UTF-8 or UTF-16(BE/LE)
    then corresponding encoding name is returned, otherwise None is returned.
    In both cases file current position is set to after-BOM bytes. The file
    must be open in binary mode and positioned at offset 0.
    """
    # try to read first three bytes
    lead = file.read(3)
    if len(lead) == 3 and lead == codecs.BOM_UTF8:
        # UTF-8, position is already OK, use canonical name
        return codecs.lookup("utf-8").name
    elif len(lead) >= 2 and lead[:2] == codecs.BOM_UTF16_BE:
        # need to backup one character
        if len(lead) == 3:
            file.seek(-1, os.SEEK_CUR)
        return codecs.lookup("utf-16-be").name
    elif len(lead) >= 2 and lead[:2] == codecs.BOM_UTF16_LE:
        # need to backup one character
        if len(lead) == 3:
            file.seek(-1, os.SEEK_CUR)
        return codecs.lookup("utf-16-le").name
    else:
        # no BOM, rewind
        file.seek(-len(lead), os.SEEK_CUR)
        return None


def guess_lineno(file: io.IOBase) -> int:
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


class BinaryFileCR(io.BufferedReader):
    """Binary file with support of CR line terminators.

    I need a binary file object with readline() method which supports all
    possible line terminators (LF, CR-LF, CR). Standard binary files have
    readline that only stops at LF (and hence CR-LF). This class adds a
    workaround for readline method to understand CR-delimited files.
    """

    CR, LF = b"\r", b"\n"

    def __init__(self, raw: io.RawIOBase | BinaryIO):
        # BufferedReader accepts RawIOBase, but for many tests we want to use
        # BinaryIO, and there is no way to convert BinaryIO to RawIOBase, but
        # it works for our purposes, so we just lie to mypy.
        io.BufferedReader.__init__(self, raw)  # type: ignore[arg-type]

    def readline(self, limit: int | None = -1) -> bytes:
        if limit == 0:
            return b""
        data: list[bytes] = []
        while True:
            byte = self.read(1)
            if not byte:
                return b"".join(data)
            data.append(byte)
            if not (limit is None or limit < 0) and len(data) >= limit:
                return b"".join(data)
            elif byte == self.LF:
                return b"".join(data)
            elif byte == self.CR:
                # look at next byte
                more_data = self.peek(1)
                if not more_data:
                    return b"".join(data)
                nxt = more_data[:1]
                if nxt == self.LF:
                    nxt = self.read(1)
                    data.append(nxt)
                return b"".join(data)
