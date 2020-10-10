#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ged4py.parser` module."""

from contextlib import contextmanager
import io
import tempfile
import os
import unittest

from ged4py import model, parser
from ged4py.detail.io import BinaryFileCR


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


def _make_file_object(data):
    """AMke file object from a byte string
    """
    return BinaryFileCR(io.BytesIO(data))


class TestParser(unittest.TestCase):
    """Tests for `ged4py.parser` module."""

    def test_002_guess_codec(self):
        """Test guess_codec()."""

        file = _make_file_object(b"0 HEAD\n1 CHAR ASCII\n0 TRLR")
        self.assertEqual(parser.guess_codec(file), ("ascii", 0))

        file = _make_file_object(b"0 HEAD\n1 CHAR ANSEL\n0 TRLR")
        self.assertEqual(parser.guess_codec(file), ("gedcom", 0))

        file = _make_file_object(b"0 HEAD\n1 CHAR UTF-8\n0 TRLR")
        self.assertEqual(parser.guess_codec(file), ("utf-8", 0))

        file = _make_file_object(b"\xef\xbb\xbf0 HEAD\n1 CHAR UTF-8\n0 TRLR")
        self.assertEqual(parser.guess_codec(file), ("utf-8", 3))

        # single CR line terminator
        file = _make_file_object(b"\xef\xbb\xbf0 HEAD\r1 CHAR UTF-8\r0 TRLR")
        self.assertEqual(parser.guess_codec(file), ("utf-8", 3))

        file = _make_file_object(b"0 HEAD\r1 CHAR ANSEL\r0 TRLR")
        self.assertEqual(parser.guess_codec(file), ("gedcom", 0))

        # CR-LF
        file = _make_file_object(b"\xef\xbb\xbf0 HEAD\r\n1 CHAR UTF-8\r\n0 TRLR")
        self.assertEqual(parser.guess_codec(file), ("utf-8", 3))

#         UTF-16 is broken
#         # utf-16-le
#         file = _make_file_object(b"\xff\xfe0\0 \0H\0E\0A\0D\n\0\x31\0 \0C\0H\0A\0R\0 \0U\0T\0F\0-\01\06\0")
#         self.assertEqual(parser.guess_codec(file), "utf-16")
#
#         # utf-16-be
#         file = _make_file_object(b"\xfe\xff\0\x30\0 \0H\0E\0A\0D")
#         self.assertEqual(parser.guess_codec(file), "utf-16")

    def test_003_codec_exceptions(self):
        """Test codecs-related exceptions."""

        # unknown codec name
        file = _make_file_object(b"0 HEAD\n1 CHAR NOTCODEC\n0 TRLR")
        self.assertRaises(parser.CodecError, parser.guess_codec, file)

        # BOM disagrees with CHAR
        file = _make_file_object(b"\xef\xbb\xbf0 HEAD\n1 CHAR ANSEL\n0 TRLR")
        self.assertRaises(parser.CodecError, parser.guess_codec, file)

    def test_010_open(self):
        """Test gedcom_open() method."""

        data = b"0 HEAD\n1 CHAR ANSEL\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                self.assertEqual(reader._encoding, "gedcom")
                self.assertEqual(reader._bom_size, 0)

        data = b"0 HEAD\n1 CHAR ASCII\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                self.assertEqual(reader._encoding, "ascii")
                self.assertEqual(reader._bom_size, 0)

        data = b"0 HEAD\n1 CHAR UTF-8\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                self.assertEqual(reader._encoding, "utf-8")
                self.assertEqual(reader._bom_size, 0)

        data = b"\xef\xbb\xbf0 HEAD\n1 CHAR UTF-8\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                self.assertEqual(reader._encoding, "utf-8")
                self.assertEqual(reader._bom_size, 3)

        # CR-LF
        data = b"\xef\xbb\xbf0 HEAD\r\n1 CHAR UTF-8\r\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                self.assertEqual(reader._encoding, "utf-8")
                self.assertEqual(reader._bom_size, 3)

        data = b"0 HEAD\n1 CHAR ASCII\n0 TRLR"
        with _make_file_object(data) as file:
            with parser.GedcomReader(file) as reader:
                self.assertEqual(reader._encoding, "ascii")
                self.assertEqual(reader._bom_size, 0)

        data = b"\xef\xbb\xbf0 HEAD\n1 CHAR UTF-8\n0 TRLR"
        with _make_file_object(data) as file:
            with parser.GedcomReader(file) as reader:
                self.assertEqual(reader._encoding, "utf-8")
                self.assertEqual(reader._bom_size, 3)

        data = b"0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                self.assertEqual(reader._encoding, "gedcom")
                self.assertEqual(reader._bom_size, 0)

        data = b"\xef\xbb\xbf0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                self.assertEqual(reader._encoding, "utf-8")
                self.assertEqual(reader._bom_size, 3)

    def test_011_open_errors(self):
        """Test gedcom_open() method."""

        # no HEAD
        data = b"\xef\xbb\xbf0 HDR\n1 CHAR ANSEL\n0 TRLR"
        with _temp_file(data) as fname:
            self.assertRaises(parser.CodecError, parser.GedcomReader, fname,
                              require_char=True)

        # no CHAR
        data = b"\xef\xbb\xbf0 HEAD\n1 NOCHAR ANSEL\n0 TRLR"
        with _temp_file(data) as fname:
            self.assertRaises(parser.CodecError, parser.GedcomReader, fname,
                              require_char=True)

        # unknown encoding
        data = b"\xef\xbb\xbf0 HEAD\n1 CHAR not-an-encoding\n0 TRLR"
        with _temp_file(data) as fname:
            self.assertRaises(parser.CodecError, parser.GedcomReader, fname)

        # expect UTF-8
        data = b"\xef\xbb\xbf0 HEAD\n1 CHAR ANSEL\n0 TRLR"
        with _temp_file(data) as fname:
            self.assertRaises(parser.CodecError, parser.GedcomReader, fname)

    def test_015_init_index(self):
        """Test _init_index() method."""

        data = b"0 HEAD\n0 @i1@ INDI\n0 @i2@ INDI\n0 @i3@ INDI\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                self.assertTrue(reader._index0 is None)
                self.assertTrue(reader._xref0 is None)
                reader._init_index()
                self.assertEqual(reader._index0, [(0, "HEAD"),
                                                  (7, "INDI"),
                                                  (19, "INDI"),
                                                  (31, "INDI"),
                                                  (43, "TRLR")])
                self.assertEqual(reader._xref0, {"@i1@": (7, "INDI"),
                                                 "@i2@": (19, "INDI"),
                                                 "@i3@": (31, "INDI")})

    def test_017_dialect(self):
        """Test dialect property."""

        data = b"0 HEAD\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                self.assertEqual(reader.dialect, model.Dialect.DEFAULT)

        data = b"0 HEAD\n1 SOUR MYHERITAGE\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                self.assertEqual(reader.dialect, model.Dialect.MYHERITAGE)

        data = b"0 HEAD\n1 SOUR ALTREE\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                self.assertEqual(reader.dialect, model.Dialect.ALTREE)

        data = b"0 HEAD\n1 SOUR AgelongTree\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                self.assertEqual(reader.dialect, model.Dialect.ALTREE)

        data = b"0 HEAD\n1 SOUR ANCESTRIS\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                self.assertEqual(reader.dialect, model.Dialect.ANCESTRIS)

        data = b"0 HEAD\n1 SOUR XXX\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                self.assertEqual(reader.dialect, model.Dialect.DEFAULT)

    def test_020_GedcomLines(self):
        """Test GedcomLines method"""

        # simple content
        data = b"0 HEAD\n1 CHAR ASCII\n1 SOUR PIF PAF\n0 @i1@ INDI\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                lines = list(reader.GedcomLines(0))
                expect = [parser.GedcomLine(level=0, xref_id=None, tag="HEAD", value=None, offset=0),
                          parser.GedcomLine(level=1, xref_id=None, tag="CHAR", value=b"ASCII", offset=7),
                          parser.GedcomLine(level=1, xref_id=None, tag="SOUR", value=b"PIF PAF", offset=20),
                          parser.GedcomLine(level=0, xref_id="@i1@", tag="INDI", value=None, offset=35),
                          parser.GedcomLine(level=0, xref_id=None, tag="TRLR", value=None, offset=47)]
                self.assertEqual(lines, expect)

        # Unicode characters
        data = b"0 HEAD\n1 CHAR UTF-8\n0 OK \xc2\xb5"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                lines = list(reader.GedcomLines(0))
                expect = [parser.GedcomLine(level=0, xref_id=None, tag="HEAD", value=None, offset=0),
                          parser.GedcomLine(level=1, xref_id=None, tag="CHAR", value=b"UTF-8", offset=7),
                          parser.GedcomLine(level=0, xref_id=None, tag="OK", value=b"\xc2\xb5", offset=20)]
                self.assertEqual(lines, expect)

        # Unicode and BOM
        data = b"\xef\xbb\xbf0 HEAD\r\n1 CHAR UTF-8\r\n0 OK \xc2\xb5"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                lines = list(reader.GedcomLines(3))
                expect = [parser.GedcomLine(level=0, xref_id=None, tag="HEAD", value=None, offset=3),
                          parser.GedcomLine(level=1, xref_id=None, tag="CHAR", value=b"UTF-8", offset=11),
                          parser.GedcomLine(level=0, xref_id=None, tag="OK", value=b"\xc2\xb5", offset=25)]
                self.assertEqual(lines, expect)

        data = b"\xef\xbb\xbf0 HEAD\r\n1 CHAR UTF-8\r\n0 OK \xc2\xb5"
        with _make_file_object(data) as file:
            with parser.GedcomReader(file) as reader:
                lines = list(reader.GedcomLines(3))
                expect = [parser.GedcomLine(level=0, xref_id=None, tag="HEAD", value=None, offset=3),
                          parser.GedcomLine(level=1, xref_id=None, tag="CHAR", value=b"UTF-8", offset=11),
                          parser.GedcomLine(level=0, xref_id=None, tag="OK", value=b"\xc2\xb5", offset=25)]
                self.assertEqual(lines, expect)

        # simple content with CR-LF terminators
        data = b"0 HEAD\r\n1 CHAR ASCII\r\n1 SOUR PIF PAF\r\n0 @i1@ INDI\r\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                lines = list(reader.GedcomLines(0))
                expect = [parser.GedcomLine(level=0, xref_id=None, tag="HEAD", value=None, offset=0),
                          parser.GedcomLine(level=1, xref_id=None, tag="CHAR", value=b"ASCII", offset=8),
                          parser.GedcomLine(level=1, xref_id=None, tag="SOUR", value=b"PIF PAF", offset=22),
                          parser.GedcomLine(level=0, xref_id="@i1@", tag="INDI", value=None, offset=38),
                          parser.GedcomLine(level=0, xref_id=None, tag="TRLR", value=None, offset=51)]
                self.assertEqual(lines, expect)

        # simple content with CR terminators
        data = b"0 HEAD\r1 CHAR ASCII\r1 SOUR PIF PAF\r0 @i1@ INDI\r0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                lines = list(reader.GedcomLines(0))
                expect = [parser.GedcomLine(level=0, xref_id=None, tag="HEAD", value=None, offset=0),
                          parser.GedcomLine(level=1, xref_id=None, tag="CHAR", value=b"ASCII", offset=7),
                          parser.GedcomLine(level=1, xref_id=None, tag="SOUR", value=b"PIF PAF", offset=20),
                          parser.GedcomLine(level=0, xref_id="@i1@", tag="INDI", value=None, offset=35),
                          parser.GedcomLine(level=0, xref_id=None, tag="TRLR", value=None, offset=47)]
                self.assertEqual(lines, expect)

    def test_021_GedcomLines_errors(self):
        """Test for exceptions raised by GedcomLines method"""

        # tag name is only letters and digits
        data = b"0 HEAD\n1 CHAR ASCII\n1 SO@UR PIF PAF"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                itr = reader.GedcomLines(0)
                self.assertRaises(parser.ParserError, list, itr)

        # xref must start with letter or digit
        data = b"0 HEAD\n1 CHAR ASCII\n1 @!ref@ SOUR PIF PAF"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                itr = reader.GedcomLines(0)
                self.assertRaises(parser.ParserError, list, itr)

        # level must be a number
        data = b"0 HEAD\n1 CHAR ASCII\nX SOUR PIF PAF"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                itr = reader.GedcomLines(0)
                self.assertRaises(parser.ParserError, list, itr)

        # consistency check - nested levels
        datas = [b"0 HEAD\n1 CHAR ASCII\n1 DATA\n3 MORE DATA",
                 b"0 HEAD\n1 CHAR ASCII\n1 DATA adata\n1 CONC aadata",
                 b"0 HEAD\n1 CHAR ASCII\n1 DATA adata\n3 CONC aadata",
                 b"0 HEAD\n1 CHAR ASCII\n1 DATA adata\n1 CONT aadata",
                 b"0 HEAD\n1 CHAR ASCII\n1 DATA adata\n3 CONT aadata",
                 b"0 HEAD\n1 CHAR ASCII\n1 DATA adata\n2 CONT aadata\n3 CONT aadata",
                 b"0 HEAD\n1 CHAR ASCII\n1 DATA adata\n2 CONT aadata\n1 CONT aadata",
                 ]
        for data in datas:
            print(data)
            with _temp_file(data) as fname:
                with parser.GedcomReader(fname) as reader:
                    itr = reader.GedcomLines(0)
                    self.assertRaises(parser.IntegrityError, list, itr)

    def test_030_read_record(self):
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

    def test_031_read_record_conc(self):
        # encoded string
        data = b"0 HEAD\n1 CHAR UTF8\n"\
            b"0 TAG \xd0\x98\xd0\xb2\xd0\xb0\xd0\xbd \xd0\x98\xd0\xb2\xd0\xb0"\
            b"\xd0\xbd\xd0\xbe\xd0\xb2\xd0\xb8\xd1\x87"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:

                note = reader.read_record(19)
                self.assertEqual(note.level, 0)
                self.assertEqual(note.tag, "TAG")
                self.assertEqual(note.value, "Иван Иванович")

        # encoded string split
        data = b"0 HEAD\n1 CHAR UTF8\n"\
            b"0 TAG \xd0\x98\xd0\xb2\xd0\xb0\xd0\xbd \xd0\x98\n"\
            b"1 CONC \xd0\xb2\xd0\xb0\xd0\xbd\xd0\xbe\xd0\xb2\xd0\xb8\xd1\x87"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:

                note = reader.read_record(19)
                self.assertEqual(note.level, 0)
                self.assertEqual(note.tag, "TAG")
                self.assertEqual(note.value, "Иван Иванович")

        # encoded string split in the middle of multi-byte character
        data = b"0 HEAD\n1 CHAR UTF8\n"\
            b"0 TAG \xd0\x98\xd0\xb2\xd0\xb0\xd0\xbd \xd0\n"\
            b"1 CONC \x98\xd0\xb2\xd0\xb0\xd0\xbd\xd0\xbe\xd0\xb2\xd0\xb8\xd1\x87"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:

                note = reader.read_record(19)
                self.assertEqual(note.level, 0)
                self.assertEqual(note.tag, "TAG")
                self.assertEqual(note.value, "Иван Иванович")

        # encoded string split in between combining characters (UTF-8)
        data = b"0 HEAD\n1 CHAR UTF8\n"\
            b"0 TAG Pa\n"\
            b"1 CONC \xcc\x8al"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:

                note = reader.read_record(19)
                self.assertEqual(note.level, 0)
                self.assertEqual(note.tag, "TAG")
                self.assertEqual(note.value, "Pål")

        # encoded string split in between combining characters (ANSEL)
        data = b"0 HEAD\n1 CHAR ANSEL\n"\
            b"0 TAG P\xea\n"\
            b"1 CONC al"

        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:

                note = reader.read_record(20)
                self.assertEqual(note.level, 0)
                self.assertEqual(note.tag, "TAG")
                self.assertEqual(note.value, "Pål")

    def test_035_read_record_errors(self):
        """Test read_record method"""

        data = b"0 HEAD\n1 CHAR ASCII\n0 INDI A\n0 INDI B"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:

                # try to read beyond EOF should return None
                rec = reader.read_record(1000)
                self.assertTrue(rec is None)

                # Random location
                self.assertRaises(parser.ParserError, reader.read_record, 26)

    def test_040_records0(self):
        """Test records0 method"""

        data = b"0 HEAD\n1 CHAR ASCII\n0 INDI A\n1 SUBA A\n1 SUBB B\n2 SUBC C\n1 SUBD D\n0 STOP"
        with _make_file_object(data) as file:
            with parser.GedcomReader(file) as reader:

                recs = list(reader.records0())
                self.assertEqual(len(recs), 3)

                rec = recs[0]
                self.assertEqual(rec.level, 0)
                self.assertEqual(rec.tag, "HEAD")
                self.assertEqual(rec.value, None)
                self.assertEqual(len(rec.sub_records), 1)
                self.assertEqual(rec.dialect, model.Dialect.DEFAULT)

                rec = recs[1]
                self.assertEqual(rec.level, 0)
                self.assertEqual(rec.tag, "INDI")
                self.assertEqual(rec.value, "A")
                self.assertEqual(len(rec.sub_records), 3)
                self.assertEqual(rec.dialect, model.Dialect.DEFAULT)

                rec = recs[2]
                self.assertEqual(rec.level, 0)
                self.assertEqual(rec.tag, "STOP")
                self.assertEqual(rec.value, None)
                self.assertEqual(len(rec.sub_records), 0)
                self.assertEqual(rec.dialect, model.Dialect.DEFAULT)

    def test_041_header(self):
        """Test header property."""

        data = b"0 HEAD\n1 SOUR ALTREE\n0 TRLR"
        with _temp_file(data) as fname:
            with parser.GedcomReader(fname) as reader:
                rec = reader.header
                self.assertEqual(rec.level, 0)
                self.assertEqual(rec.tag, "HEAD")
                self.assertEqual(rec.value, None)
                self.assertEqual(len(rec.sub_records), 1)
                self.assertEqual(rec.dialect, model.Dialect.DEFAULT)

    def test_042_rec_dialect(self):
        """Test records0 method"""

        data = b"0 HEAD\n1 CHAR ASCII\n1 SOUR ALTREE\n"\
            b"0 INDI A\n1 SUBA A\n1 SUBB B\n2 SUBC C\n1 SUBD D\n0 STOP"
        with _make_file_object(data) as file:
            with parser.GedcomReader(file) as reader:

                recs = list(reader.records0())
                self.assertEqual(len(recs), 3)

                rec = recs[0]
                self.assertEqual(rec.level, 0)
                self.assertEqual(rec.tag, "HEAD")
                self.assertEqual(rec.value, None)
                self.assertEqual(len(rec.sub_records), 2)
                self.assertEqual(rec.dialect, model.Dialect.DEFAULT)

                rec = recs[1]
                self.assertEqual(rec.level, 0)
                self.assertEqual(rec.tag, "INDI")
                self.assertEqual(rec.value, "A")
                self.assertEqual(len(rec.sub_records), 3)
                self.assertEqual(rec.dialect, model.Dialect.ALTREE)

                rec = recs[2]
                self.assertEqual(rec.level, 0)
                self.assertEqual(rec.tag, "STOP")
                self.assertEqual(rec.value, None)
                self.assertEqual(len(rec.sub_records), 0)
                self.assertEqual(rec.dialect, model.Dialect.ALTREE)
