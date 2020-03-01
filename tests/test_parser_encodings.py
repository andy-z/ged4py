#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for ged4py encodings handling."""

import io
import logging
import pytest

from ged4py.parser import GedcomReader, CodecError


def _check_log_rec(rec, level, msg, args):
    assert rec.levelno == level
    assert msg in rec.msg
    assert rec.args == args


def test_001_standard():
    """Test standard encodings."""

    file = io.BytesIO(b"0 HEAD\n1 CHAR ASCII\n0 TRLR")
    reader = GedcomReader(file)
    assert reader._encoding == "ascii"

    file = io.BytesIO(b"0 HEAD\n1 CHAR ANSEL\n0 TRLR")
    reader = GedcomReader(file)
    assert reader._encoding == "gedcom"

    file = io.BytesIO(b"0 HEAD\n1 CHAR UTF-8\n0 TRLR")
    reader = GedcomReader(file)
    assert reader._encoding == "utf-8"

    file = io.BytesIO(b"\xef\xbb\xbf0 HEAD\n1 CHAR UTF-8\n0 TRLR")
    reader = GedcomReader(file)
    assert reader._encoding == "utf-8"

    # UTF-16 is broken, do not use


@pytest.mark.parametrize('enc,pyenc,ambig',
                         [("IBMPC", "cp437", True),
                          ("IBM", "cp437", True),
                          ("IBM-PC", "cp437", True),
                          ("OEM", "cp437", True),
                          ("MSDOS", "cp850", True),
                          ("IBM DOS", "cp850", True),
                          ("MS-DOS", "cp850", True),
                          ("ANSI", "cp1252", True),
                          ("WINDOWS", "cp1252", True),
                          ("IBM WINDOWS", "cp1252", True),
                          ("IBM_WINDOWS", "cp1252", True),
                          ("WINDOWS-1250", "cp1250", False),
                          ("WINDOWS-1251", "cp1251", False),
                          ("CP1252", "cp1252", False),
                          ("ISO-8859-1", "iso8859-1", False),
                          ("ISO8859-1", "iso8859-1", False),
                          ("ISO8859", "iso8859-1", True),
                          ("LATIN1", "iso8859-1", True),
                          ("MACINTOSH", "mac-roman", True),
                          ])
def test_002_illegal(enc, pyenc, ambig, caplog):
    """Test for illegal encodings.
    """
    caplog.set_level(logging.WARNING)

    # %s formatting works in py27 and py3
    char = ("1 CHAR " + enc).encode()
    file = io.BytesIO(b"0 HEAD\n" + char + b"\n0 TRLR")
    reader = GedcomReader(file)
    assert reader._encoding == pyenc

    # check logging
    assert len(caplog.records) == (2 if ambig else 1)
    _check_log_rec(caplog.records[0], logging.ERROR,
                   "is not a legal character set or encoding",
                   (2, char, enc))
    if ambig:
        _check_log_rec(caplog.records[1], logging.WARNING,
                       "is ambiguous, it will be interpreted as",
                       (enc, pyenc))


def test_003_codec_exceptions():
    """Test codecs-related exceptions."""

    # unknown codec name
    file = io.BytesIO(b"0 HEAD\n1 CHAR NOTCODEC\n0 TRLR")
    with pytest.raises(CodecError):
        GedcomReader(file)

    # BOM disagrees with CHAR
    file = io.BytesIO(b"\xef\xbb\xbf0 HEAD\n1 CHAR ANSEL\n0 TRLR")
    with pytest.raises(CodecError):
        GedcomReader(file)
