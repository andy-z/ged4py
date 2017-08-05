#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ged4py.codecs` module."""

from contextlib import contextmanager
import io
import tempfile
import os
import unittest
import sys


from ged4py import parser
from ged4py.detail.io import check_bom


@contextmanager
def _temp_file(data):
    """Create file with unique name and store some data in it.

    Returns file name.
    """
    fd, fname = tempfile.mkstemp()
    os.write(fd, data)
    os.close(fd)
    yield fname
    os.unlink(fname)


class TestParser(unittest.TestCase):
    """Tests for `ged4py.parser` module."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_001_guess_bom_codec(self):
        """Test detail.check_bom()."""

        file = io.BytesIO(b"0 HEAD")
        codec = check_bom(file)
        self.assertTrue(codec is None)
        self.assertEqual(file.tell(), 0)

        file = io.BytesIO(b"0")
        codec = check_bom(file)
        self.assertTrue(codec is None)
        self.assertEqual(file.tell(), 0)

        file = io.BytesIO(b"\xef\xbb\xbf0 HEAD")
        codec = check_bom(file)
        self.assertEqual(codec, "utf-8")
        self.assertEqual(file.tell(), 3)

        file = io.BytesIO(b"\xff\xfe0 HEAD")
        codec = check_bom(file)
        self.assertEqual(codec, "utf-16-le")
        self.assertEqual(file.tell(), 2)

        file = io.BytesIO(b"\xfe\xff0 HEAD")
        codec = check_bom(file)
        self.assertEqual(codec, "utf-16-be")
        self.assertEqual(file.tell(), 2)

        file = io.BytesIO(b"\xfe\xff")
        codec = check_bom(file)
        self.assertEqual(codec, "utf-16-be")
        self.assertEqual(file.tell(), 2)

    def test_002_guess_codec(self):
        """Test guess_codec()."""

        file = io.BytesIO(b"0 HEAD\n1 CHAR ASCII\n0 TRLR")
        self.assertEqual(parser.guess_codec(file), "ascii")

        file = io.BytesIO(b"0 HEAD\n1 CHAR UTF-8\n0 TRLR")
        self.assertEqual(parser.guess_codec(file), "utf-8")

        file = io.BytesIO(b"\xef\xbb\xbf0 HEAD\n1 CHAR UTF-8\n0 TRLR")
        self.assertEqual(parser.guess_codec(file), "utf-8-sig")

#         UTF-16 is broken
#         # utf-16-le
#         file = io.BytesIO(b"\xff\xfe0\0 \0H\0E\0A\0D\n\0\x31\0 \0C\0H\0A\0R\0 \0U\0T\0F\0-\01\06\0")
#         self.assertEqual(parser.guess_codec(file), "utf-16")
#
#         # utf-16-be
#         file = io.BytesIO(b"\xfe\xff\0\x30\0 \0H\0E\0A\0D")
#         self.assertEqual(parser.guess_codec(file), "utf-16")

    def test_003_codec_exceptions(self):
        """Test codecs-related exceptions."""

        # unknown codec name
        file = io.BytesIO(b"0 HEAD\n1 CHAR NOTCODEC\n0 TRLR")
        self.assertRaises(parser.CodecError, parser.guess_codec, file)

        # BOM disagrees with CHAR
        file = io.BytesIO(b"\xef\xbb\xbf0 HEAD\n1 CHAR ANSEL\n0 TRLR")
        self.assertRaises(parser.CodecError, parser.guess_codec, file)

        # Initial ANSEL cannot decode some characters
        file = io.BytesIO(b"0 HEAD\n0 OK \xc7")
        self.assertRaises(UnicodeDecodeError, parser.guess_codec, file)

    def test_004_open(self):
        """Test open() method."""

        data = b"0 HEAD\n1 CHAR ANSEL\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.open(fname) as file:
                self.assertEqual(file.encoding, "ansel")
                self.assertEqual(file.tell(), 0)
                self.assertEqual(list(file.readlines()), ["0 HEAD\n", "1 CHAR ANSEL\n", "0 TRLR"])

        data = b"0 HEAD\n1 CHAR ASCII\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.open(fname) as file:
                self.assertEqual(file.encoding, "ascii")
                self.assertEqual(file.tell(), 0)
                self.assertEqual(list(file.readlines()), ["0 HEAD\n", "1 CHAR ASCII\n", "0 TRLR"])

        data = b"0 HEAD\n1 CHAR UTF-8\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.open(fname) as file:
                self.assertEqual(file.encoding, "utf-8")
                self.assertEqual(file.tell(), 0)
                self.assertEqual(list(file.readlines()), ["0 HEAD\n", "1 CHAR UTF-8\n", "0 TRLR"])

        data = b"\xef\xbb\xbf0 HEAD\n1 CHAR UTF-8\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.open(fname) as file:
                self.assertEqual(file.encoding, "utf-8-sig")
                self.assertEqual(file.tell(), 0)
                self.assertEqual(list(file.readlines()), ["0 HEAD\n", "1 CHAR UTF-8\n", "0 TRLR"])

    def test_005_open_errors(self):
        """Test open() method."""

        # no HEAD
        data = b"\xef\xbb\xbf0 HDR\n1 CHAR ANSEL\n0 TRLR"
        with _temp_file(data) as fname:
            self.assertRaises(parser.CodecError, parser.open, fname)

        # no CHAR
        data = b"\xef\xbb\xbf0 HEAD\n1 NOCHAR ANSEL\n0 TRLR"
        with _temp_file(data) as fname:
            self.assertRaises(parser.CodecError, parser.open, fname)

        # unknown encoding
        data = b"\xef\xbb\xbf0 HEAD\n1 CHAR not-an-encoding\n0 TRLR"
        with _temp_file(data) as fname:
            self.assertRaises(parser.CodecError, parser.open, fname)

        # expect UTF-8
        data = b"\xef\xbb\xbf0 HEAD\n1 CHAR ANSEL\n0 TRLR"
        with _temp_file(data) as fname:
            self.assertRaises(parser.CodecError, parser.open, fname)

    def test_006_gedcom_lines(self):
        """Test gedcom_lines method"""

        # simple content
        data = b"0 HEAD\n1 CHAR ASCII\n1 SOUR PIF PAF\n0 @i1@ INDI\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.open(fname) as file:
                lines = list(parser.gedcom_lines(file))
                expect = [parser.gedcom_line(level=0, xref_id=None, tag="HEAD", value=None, offset=0),
                          parser.gedcom_line(level=1, xref_id=None, tag="CHAR", value="ASCII", offset=7),
                          parser.gedcom_line(level=1, xref_id=None, tag="SOUR", value="PIF PAF", offset=20),
                          parser.gedcom_line(level=0, xref_id="@i1@", tag="INDI", value=None, offset=35),
                          parser.gedcom_line(level=0, xref_id=None, tag="TRLR", value=None, offset=47)]
                self.assertEqual(lines, expect)

        # Unicode characters
        data = b"0 HEAD\n1 CHAR UTF-8\n0 OK \xc2\xb5"
        with _temp_file(data) as fname:
            with parser.open(fname) as file:
                lines = list(parser.gedcom_lines(file))
                expect = [parser.gedcom_line(level=0, xref_id=None, tag="HEAD", value=None, offset=0),
                          parser.gedcom_line(level=1, xref_id=None, tag="CHAR", value="UTF-8", offset=7),
                          parser.gedcom_line(level=0, xref_id=None, tag="OK", value=u"\u00b5", offset=20)]
                self.assertEqual(lines, expect)

        # Unicode and BOM
        data = b"\xef\xbb\xbf0 HEAD\n1 CHAR UTF-8\n0 OK \xc2\xb5"
        with _temp_file(data) as fname:
            with parser.open(fname) as file:
                lines = list(parser.gedcom_lines(file))
                # in 2.6 offset is messed up (off by -1)
                doff = -1 if sys.hexversion & 0xFFFF0000 == 0x02060000 else 0
                expect = [parser.gedcom_line(level=0, xref_id=None, tag="HEAD", value=None, offset=0),
                          parser.gedcom_line(level=1, xref_id=None, tag="CHAR", value="UTF-8", offset=10 + doff),
                          parser.gedcom_line(level=0, xref_id=None, tag="OK", value=u"\u00b5", offset=23 + doff)]
                self.assertEqual(lines, expect)

    def test_007_gedcom_lines_errors(self):
        """Test gedcom_lines method"""

        # tag name is only letters and digits
        data = b"0 HEAD\n1 CHAR ASCII\n1 SO@UR PIF PAF"
        with _temp_file(data) as fname:
            with parser.open(fname) as file:
                iter = parser.gedcom_lines(file)
                self.assertRaises(parser.ParserError, list, iter)

        # xref must start with letter or digit
        data = b"0 HEAD\n1 CHAR ASCII\n1 @!ref@ SOUR PIF PAF"
        with _temp_file(data) as fname:
            with parser.open(fname) as file:
                iter = parser.gedcom_lines(file)
                self.assertRaises(parser.ParserError, list, iter)

        # level must be a number
        data = b"0 HEAD\n1 CHAR ASCII\nX SOUR PIF PAF"
        with _temp_file(data) as fname:
            with parser.open(fname) as file:
                iter = parser.gedcom_lines(file)
                self.assertRaises(parser.ParserError, list, iter)
