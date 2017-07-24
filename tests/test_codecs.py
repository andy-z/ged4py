#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ged4py.codecs` module."""

import codecs
import unittest

# import of `codecs` is enough to register new codec
import ged4py.codecs  # noqa: F401


class TestCodecs(unittest.TestCase):
    """Tests for `ged4py` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_lookup(self):
        """Test lookup."""
        self.assertTrue(codecs.lookup("ansel") is not None)
        self.assertTrue(codecs.lookup("ANSEL") is not None)

    def test_001_encode(self):
        """Test encode()."""

        res = codecs.encode(u"Aabcd0123$%", 'ansel')
        self.assertEqual(res, b"Aabcd0123$%")

        res = codecs.encode(u"ŁØĐÞÆŒ♭®ƠƯ", 'ansel')
        self.assertEqual(res, b"\xa1\xa2\xa3\xa4\xa5\xa6\xa9\xaa\xac\xad")
        res = codecs.encode(u"łøđþæœı£ðơư", 'ansel')
        self.assertEqual(res, b"\xb1\xb2\xb3\xb4\xb5\xb6\xb8\xb9\xba\xbc\xbd")
        res = codecs.encode(u"°ℓ℗©♯¿¡", 'ansel')
        self.assertEqual(res, b"\xc0\xc1\xc2\xc3\xc4\xc5\xc6")
        res = codecs.encode(u"\u0303a", 'ansel')
        self.assertEqual(res, b"\xe4a")

    def test_002_decode(self):
        """Test decode()."""

        res = codecs.decode(b"Aabcd0123$%", 'ansel')
        self.assertEqual(res, u"Aabcd0123$%")

        res = codecs.decode(b"\xa1\xa2\xa3\xa4\xa5\xa6\xa9\xaa\xac\xad",
                            'ansel')
        self.assertEqual(res, u"ŁØĐÞÆŒ♭®ƠƯ")
        res = codecs.decode(b"\xb1\xb2\xb3\xb4\xb5\xb6\xb8\xb9\xba\xbc\xbd",
                            'ansel')
        self.assertEqual(res, u"łøđþæœı£ðơư")
        res = codecs.decode(b"\xc0\xc1\xc2\xc3\xc4\xc5\xc6", 'ansel')
        self.assertEqual(res, u"°ℓ℗©♯¿¡")
        res = codecs.decode(b"\xe4a", 'ansel')
        self.assertEqual(res, u"\u0303a")

    def test_003_encerrors(self):
        """Test encoding errors"""

        self.assertRaises(UnicodeEncodeError, codecs.encode, u"Привет",
                          'ansel', 'strict')

        res = codecs.encode(u"Привет Andy", 'ansel', 'ignore')
        self.assertEqual(res, b" Andy")
        res = codecs.encode(u"Привет Andy", 'ansel', 'replace')
        self.assertEqual(res, b"?????? Andy")

    def test_004_decerrors(self):
        """Test decoding errors"""

        self.assertRaises(UnicodeDecodeError, codecs.decode,
                          b"\xa1\xa2\xd0\xd1", 'ansel', 'strict')

        res = codecs.decode(b"\xa1\xa2\xd0\xd1", 'ansel', 'ignore')
        self.assertEqual(res, u"ŁØ")
        res = codecs.decode(b"\xa1\xa2\xd0\xd1", 'ansel', 'replace')
        self.assertEqual(res, u"ŁØ\ufffd\ufffd")
