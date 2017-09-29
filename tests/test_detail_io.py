#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ged4py.detail.io` module."""

from contextlib import contextmanager
import io
import tempfile
import os
import unittest

from ged4py.detail.io import check_bom, guess_lineno


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


class TestDetailIo(unittest.TestCase):
    """Tests for `ged4py.detail.io` module."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_001_guess_bom_codec(self):
        """Test detail.io.check_bom()."""

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

    def test_002_guess_lineno(self):
        """Test detail.io.guess_lineno()."""

        file = io.BytesIO(b"line1\nline2\nline3\nline4\nline5\n")
        file.readline()
        self.assertEqual(file.tell(), 6)
        self.assertEqual(guess_lineno(file), 2)
        self.assertEqual(file.tell(), 6)

        file.readline()
        self.assertEqual(file.tell(), 12)
        self.assertEqual(guess_lineno(file), 3)
        self.assertEqual(file.tell(), 12)

        file.readline()
        self.assertEqual(file.tell(), 18)
        self.assertEqual(guess_lineno(file), 4)
        self.assertEqual(file.tell(), 18)

        file.readline()
        self.assertEqual(file.tell(), 24)
        self.assertEqual(guess_lineno(file), 5)
        self.assertEqual(file.tell(), 24)

        file.readline()
        self.assertEqual(file.tell(), 30)
        self.assertEqual(guess_lineno(file), 6)
        self.assertEqual(file.tell(), 30)

        file.readline()
        self.assertEqual(file.tell(), 30)
        self.assertEqual(guess_lineno(file), 6)
        self.assertEqual(file.tell(), 30)

        file.seek(0)
        self.assertEqual(file.tell(), 0)
        self.assertEqual(guess_lineno(file), 1)
        self.assertEqual(file.tell(), 0)
