#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ged4py.codecs` module."""

import codecs
import unittest
import io


from ged4py import parser


class TestParser(unittest.TestCase):
    """Tests for `ged4py.parser` module."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_guess_initial_codec(self):
        """Test _guess_initial_codec()."""

        file = io.BytesIO(b"0 HEAD")
        codec = parser._guess_initial_codec(file)
        self.assertTrue(codec is None)
        self.assertEqual(file.tell(), 0)

        file = io.BytesIO(b"0")
        codec = parser._guess_initial_codec(file)
        self.assertTrue(codec is None)
        self.assertEqual(file.tell(), 0)

        file = io.BytesIO(b"\xef\xbb\xbf0 HEAD")
        codec = parser._guess_initial_codec(file)
        self.assertEqual(codec, "utf-8")
        self.assertEqual(file.tell(), 3)

        file = io.BytesIO(b"\xff\xfe0 HEAD")
        codec = parser._guess_initial_codec(file)
        self.assertEqual(codec, "utf-16-le")
        self.assertEqual(file.tell(), 2)

        file = io.BytesIO(b"\xfe\xff0 HEAD")
        codec = parser._guess_initial_codec(file)
        self.assertEqual(codec, "utf-16-be")
        self.assertEqual(file.tell(), 2)

        file = io.BytesIO(b"\xfe\xff")
        codec = parser._guess_initial_codec(file)
        self.assertEqual(codec, "utf-16-be")
        self.assertEqual(file.tell(), 2)

    def test_001_readlines(self):
        """Test readlines()."""

        file = io.BytesIO(b"0 HEAD")
        lines = list(parser.readlines(file))
        self.assertEqual(lines, ["0 HEAD"])

        file = io.BytesIO(b"0 HEAD\n1 SOUR PAF\n2 VERS 2.1\n1 DEST ANSTFILE\n0 TRLR")
        lines = list(parser.readlines(file))
        self.assertEqual(lines, ["0 HEAD", "1 SOUR PAF", "2 VERS 2.1", "1 DEST ANSTFILE", "0 TRLR"])

        file = io.BytesIO(b"\xef\xbb\xbf0 HEAD\n1 SOUR PAF\n2 VERS 2.1\n1 DEST ANSTFILE\n0 TRLR")
        lines = list(parser.readlines(file))
        self.assertEqual(lines, ["0 HEAD", "1 SOUR PAF", "2 VERS 2.1", "1 DEST ANSTFILE", "0 TRLR"])

    def test_002_codecs(self):
        """Test readlines()."""

        file = io.BytesIO(b"0 HEAD\n1 CHAR ASCII\n0 TRLR")
        lines = list(parser.readlines(file))
        self.assertEqual(lines, ["0 HEAD", "1 CHAR ASCII", "0 TRLR"])

        file = io.BytesIO(b"0 HEAD\n1 CHAR UTF-8\n0 TRLR")
        lines = list(parser.readlines(file))
        self.assertEqual(lines, ["0 HEAD", "1 CHAR UTF-8", "0 TRLR"])

        file = io.BytesIO(b"\xef\xbb\xbf0 HEAD\n1 CHAR UTF-8\n0 TRLR")
        lines = list(parser.readlines(file))
        self.assertEqual(lines, ["0 HEAD", "1 CHAR UTF-8", "0 TRLR"])

        # after switch to UTF can decode non-ANSEL stuff
        file = io.BytesIO(b"0 HEAD\n1 CHAR UTF-8\n0 OK \xc2\xb5")
        lines = list(parser.readlines(file))
        self.assertEqual(lines, ["0 HEAD", "1 CHAR UTF-8", u"0 OK \u00b5"])

        # utf-16-le
        file = io.BytesIO(b"\xff\xfe0\0 \0H\0E\0A\0D\0")
        lines = list(parser.readlines(file))
        self.assertEqual(lines, ["0 HEAD"])

        # utf-16-be
        file = io.BytesIO(b"\xfe\xff\0\x30\0 \0H\0E\0A\0D")
        lines = list(parser.readlines(file))
        self.assertEqual(lines, ["0 HEAD"])


    def test_003_codec_exceptions(self):
        """Test codecs-related exceptions."""

        # unknown codec name
        file = io.BytesIO(b"0 HEAD\n1 CHAR NOTCODEC\n0 TRLR")
        iter = parser.readlines(file)
        self.assertRaises(parser.CodecError, list, iter)

        # BOM disagrees with CHAR
        file = io.BytesIO(b"\xef\xbb\xbf0 HEAD\n1 CHAR ANSEL\n0 TRLR")
        iter = parser.readlines(file)
        self.assertRaises(parser.CodecError, list, iter)

        # Initial ANSEL cannot decode some characters
        file = io.BytesIO(b"0 HEAD\n0 OK \xc7")
        iter = parser.readlines(file)
        self.assertRaises(UnicodeDecodeError, list, iter)

    def test_003_codec_errors(self):
        """Test codec error hadling."""

        file = io.BytesIO(b"0 HEAD\n0 OK \xc7")
        iter = parser.readlines(file, 'strict')
        self.assertRaises(UnicodeDecodeError, list, iter)

        file = io.BytesIO(b"0 HEAD\n0 OK \xc7")
        iter = parser.readlines(file, 'ignore')
        self.assertEqual(list(iter), ["0 HEAD", "0 OK "])

        file = io.BytesIO(b"0 HEAD\n0 OK \xc7")
        iter = parser.readlines(file, 'replace')
        self.assertEqual(list(iter), ["0 HEAD", u"0 OK \ufffd"])
