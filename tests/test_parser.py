#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ged4py.codecs` module."""

from contextlib import contextmanager
import io
import tempfile
import os
import unittest


from ged4py import parser


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

    def test_002_guess_codec(self):
        """Test guess_codec()."""

        file = io.BytesIO(b"0 HEAD\n1 CHAR ASCII\n0 TRLR")
        self.assertEqual(parser.guess_codec(file), "ascii")

        file = io.BytesIO(b"0 HEAD\n1 CHAR UTF-8\n0 TRLR")
        self.assertEqual(parser.guess_codec(file), "utf-8")

        file = io.BytesIO(b"\xef\xbb\xbf0 HEAD\n1 CHAR UTF-8\n0 TRLR")
        self.assertEqual(parser.guess_codec(file), "utf-8-sig")

        # CR-LF
        file = io.BytesIO(b"\xef\xbb\xbf0 HEAD\r\n1 CHAR UTF-8\r\n0 TRLR")
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
        """Test gedcom_open() method."""

        data = b"0 HEAD\n1 CHAR ANSEL\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.gedcom_open(fname) as file:
                self.assertEqual(file.encoding, "ansel")
                self.assertEqual(file.tell(), 0)
                self.assertEqual(list(file.readlines()), ["0 HEAD\n", "1 CHAR ANSEL\n", "0 TRLR"])

        data = b"0 HEAD\n1 CHAR ASCII\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.gedcom_open(fname) as file:
                self.assertEqual(file.encoding, "ascii")
                self.assertEqual(file.tell(), 0)
                self.assertEqual(list(file.readlines()), ["0 HEAD\n", "1 CHAR ASCII\n", "0 TRLR"])

        data = b"0 HEAD\n1 CHAR UTF-8\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.gedcom_open(fname) as file:
                self.assertEqual(file.encoding, "utf-8")
                self.assertEqual(file.tell(), 0)
                self.assertEqual(list(file.readlines()), ["0 HEAD\n", "1 CHAR UTF-8\n", "0 TRLR"])

        data = b"\xef\xbb\xbf0 HEAD\n1 CHAR UTF-8\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.gedcom_open(fname) as file:
                self.assertEqual(file.encoding, "utf-8-sig")
                self.assertEqual(file.tell(), 0)
                self.assertEqual(list(file.readlines()), ["0 HEAD\n", "1 CHAR UTF-8\n", "0 TRLR"])

        # CR-LF
        data = b"\xef\xbb\xbf0 HEAD\r\n1 CHAR UTF-8\r\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.gedcom_open(fname) as file:
                self.assertEqual(file.encoding, "utf-8-sig")
                self.assertEqual(file.tell(), 0)
                self.assertEqual(list(file.readlines()), ["0 HEAD\n", "1 CHAR UTF-8\n", "0 TRLR"])

    def test_005_open_errors(self):
        """Test gedcom_open() method."""

        # no HEAD
        data = b"\xef\xbb\xbf0 HDR\n1 CHAR ANSEL\n0 TRLR"
        with _temp_file(data) as fname:
            self.assertRaises(parser.CodecError, parser.gedcom_open, fname)

        # no CHAR
        data = b"\xef\xbb\xbf0 HEAD\n1 NOCHAR ANSEL\n0 TRLR"
        with _temp_file(data) as fname:
            self.assertRaises(parser.CodecError, parser.gedcom_open, fname)

        # unknown encoding
        data = b"\xef\xbb\xbf0 HEAD\n1 CHAR not-an-encoding\n0 TRLR"
        with _temp_file(data) as fname:
            self.assertRaises(parser.CodecError, parser.gedcom_open, fname)

        # expect UTF-8
        data = b"\xef\xbb\xbf0 HEAD\n1 CHAR ANSEL\n0 TRLR"
        with _temp_file(data) as fname:
            self.assertRaises(parser.CodecError, parser.gedcom_open, fname)

    def test_006_gedcom_lines(self):
        """Test gedcom_lines method"""

        # simple content
        data = b"0 HEAD\n1 CHAR ASCII\n1 SOUR PIF PAF\n0 @i1@ INDI\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.gedcom_open(fname) as file:
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
            with parser.gedcom_open(fname) as file:
                lines = list(parser.gedcom_lines(file))
                expect = [parser.gedcom_line(level=0, xref_id=None, tag="HEAD", value=None, offset=0),
                          parser.gedcom_line(level=1, xref_id=None, tag="CHAR", value="UTF-8", offset=7),
                          parser.gedcom_line(level=0, xref_id=None, tag="OK", value=u"\u00b5", offset=20)]
                self.assertEqual(lines, expect)

        # Unicode and BOM
        data = b"\xef\xbb\xbf0 HEAD\r\n1 CHAR UTF-8\r\n0 OK \xc2\xb5"
        with _temp_file(data) as fname:
            with parser.gedcom_open(fname) as file:
                lines = list(parser.gedcom_lines(file))
                expect = [parser.gedcom_line(level=0, xref_id=None, tag="HEAD", value=None, offset=0),
                          parser.gedcom_line(level=1, xref_id=None, tag="CHAR", value="UTF-8", offset=11),
                          parser.gedcom_line(level=0, xref_id=None, tag="OK", value=u"\u00b5", offset=25)]
                self.assertEqual(lines, expect)

    def test_007_gedcom_lines_errors(self):
        """Test gedcom_lines method"""

        # tag name is only letters and digits
        data = b"0 HEAD\n1 CHAR ASCII\n1 SO@UR PIF PAF"
        with _temp_file(data) as fname:
            with parser.gedcom_open(fname) as file:
                iter = parser.gedcom_lines(file)
                self.assertRaises(parser.ParserError, list, iter)

        # xref must start with letter or digit
        data = b"0 HEAD\n1 CHAR ASCII\n1 @!ref@ SOUR PIF PAF"
        with _temp_file(data) as fname:
            with parser.gedcom_open(fname) as file:
                iter = parser.gedcom_lines(file)
                self.assertRaises(parser.ParserError, list, iter)

        # level must be a number
        data = b"0 HEAD\n1 CHAR ASCII\nX SOUR PIF PAF"
        with _temp_file(data) as fname:
            with parser.gedcom_open(fname) as file:
                iter = parser.gedcom_lines(file)
                self.assertRaises(parser.ParserError, list, iter)

    def test_010_read_record(self):
        """Test read_record method"""

        data = b"0 HEAD\n1 CHAR ASCII\n0 INDI A\n0 INDI B"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:

                rec = reader.read_record(20)
                self.assertEqual(rec.level, 0)
                self.assertEqual(rec.tag, "INDI")
                self.assertEqual(rec.value, "A")
                self.assertEqual(rec.sub_records, [])

                rec = reader.read_record(29)
                self.assertEqual(rec.level, 0)
                self.assertEqual(rec.tag, "INDI")
                self.assertEqual(rec.value, "B")
                self.assertEqual(rec.sub_records, [])

        data = b"0 HEAD\n1 CHAR ASCII\n0 INDI A\n1 SUBA A\n1 SUBB B\n2 SUBC C\n1 SUBD D\n0 STOP"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:

                rec = reader.read_record(20)
                self.assertEqual(rec.level, 0)
                self.assertEqual(rec.tag, "INDI")
                self.assertEqual(rec.value, "A")
                self.assertEqual(len(rec.sub_records), 3)

                suba = rec.sub_records[0]
                self.assertEqual(suba.level, 1)
                self.assertEqual(suba.tag, "SUBA")
                self.assertEqual(suba.value, "A")
                self.assertEqual(len(suba.sub_records), 0)

                subb = rec.sub_records[1]
                self.assertEqual(subb.level, 1)
                self.assertEqual(subb.tag, "SUBB")
                self.assertEqual(subb.value, "B")
                self.assertEqual(len(subb.sub_records), 1)

                subc = subb.sub_records[0]
                self.assertEqual(subc.level, 2)
                self.assertEqual(subc.tag, "SUBC")
                self.assertEqual(subc.value, "C")
                self.assertEqual(len(subc.sub_records), 0)

                subd = rec.sub_records[2]
                self.assertEqual(subd.level, 1)
                self.assertEqual(subd.tag, "SUBD")
                self.assertEqual(subd.value, "D")
                self.assertEqual(len(subd.sub_records), 0)

        data = b"0 HEAD\n1 CHAR ASCII\n0 INDI A\n1 NOTE A\n2 CONC B\n2 CONT C\n2 CONC D"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:

                rec = reader.read_record(20)
                self.assertEqual(rec.level, 0)
                self.assertEqual(rec.tag, "INDI")
                self.assertEqual(rec.value, "A")
                self.assertEqual(len(rec.sub_records), 1)

                note = rec.sub_records[0]
                self.assertEqual(note.level, 1)
                self.assertEqual(note.tag, "NOTE")
                self.assertEqual(note.value, "AB\nCD")
                self.assertEqual(len(note.sub_records), 0)

        # Space-aware concatenation
        data = b"0 HEAD\n1 CHAR ASCII\n0 INDI A\n1 NOTE\n2 CONC B\n2 CONT C\n2 CONC  D"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:

                note = reader.read_record(29)
                self.assertEqual(note.level, 1)
                self.assertEqual(note.tag, "NOTE")
                self.assertEqual(note.value, "B\nC D")
                self.assertEqual(len(note.sub_records), 0)

        # BLOB
        data = b"0 HEAD\n1 CHAR ASCII\n0 INDI A\n1 BLOB\n2 CONT A\n2 CONT B"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:

                note = reader.read_record(29)
                self.assertEqual(note.level, 1)
                self.assertEqual(note.tag, "BLOB")
                self.assertIsNone(note.value)
                self.assertEqual(len(note.sub_records), 0)

    def test_011_read_record_errors(self):
        """Test read_record method"""

        data = b"0 HEAD\n1 CHAR ASCII\n0 INDI A\n0 INDI B"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:

                # try to read beyond EOF should return None
                rec = reader.read_record(1000)
                self.assertTrue(rec is None)

                # Random location
                self.assertRaises(parser.ParserError, reader.read_record, 26)

    def test_020_records0(self):
        """Test records0 method"""

        data = b"0 HEAD\n1 CHAR ASCII\n0 INDI A\n1 SUBA A\n1 SUBB B\n2 SUBC C\n1 SUBD D\n0 STOP"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:

                recs = list(reader.records0())
                self.assertEqual(len(recs), 3)

                rec = recs[0]
                self.assertEqual(rec.level, 0)
                self.assertEqual(rec.tag, "HEAD")
                self.assertEqual(rec.value, None)
                self.assertEqual(len(rec.sub_records), 1)

                rec = recs[1]
                self.assertEqual(rec.level, 0)
                self.assertEqual(rec.tag, "INDI")
                self.assertEqual(rec.value, "A")
                self.assertEqual(len(rec.sub_records), 3)

                rec = recs[2]
                self.assertEqual(rec.level, 0)
                self.assertEqual(rec.tag, "STOP")
                self.assertEqual(rec.value, None)
                self.assertEqual(len(rec.sub_records), 0)
