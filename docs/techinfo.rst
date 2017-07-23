.. highlight:: shell

=====================
Technical information
=====================


Character encoding
------------------

GEDCOM originally provided very little support for non-Latin alphabets.
To support Latin-based characters beyond ASCII set GEDCOM used `ANSEL`_
8-bit encoding which added a bunch of diacritical marks (modifiers) and
few commonly used non-ASCI characters. Support for non-Latin characters
was added in latter version of GEDCOM standard, version 5.3 added wording
for UNICODE support (mostly broken) and draft 5.5.1 improved situation by
declaring UTF-8 encoding as supported UNICODE encoding. Several systems
producing GEDCOM output today seem to have converged on UTF-8.

The encoding of GEDCOM file is determined by the content of the file
itself, in particular by the ``CHAR`` record in the header (which is a
required record), e.g.::

    0 HEAD
      1 SOUR PAF
        2 VERS 2.1
      1 DEST ANSTFILE
      1 CHAR ANSEL

GEDCOM standard seems to imply that character set specified in ``CHAR``
record applies to everything after that record and until ``TRLR`` record
(last record in file). My interpretation of that statement is that
all header records before and including ``CHAR`` should be encoded with
default ANSEL encoding. This may be a source of incompatibilities, I can
imagine that software encoding its output in e.g. UTF-8 can decide to
encode all header records in the the same UTF-8 which can cause errors if
decoded using ANSEL.

Additional source of concerns is the `BOM`_ record that some applications
(or many on Windows) tend to add to files encoded with UTF-8 (or UTF-16).
Presence of BOM usually implies that the whole content of the file should
be decoded using UTF-8/-16. This contradicts assumption that initial part
of GEDCOM header is encoded in ANSEL.

Ged4py tries to make a best guess as to how it should decode input data,
and it uses simple algorithm to determine that:

- if file starts with `BOM`_ record then ged4py reads the whole file using
  UTF-8 or UTF-16 encoding, if the ``CHAR`` record specifies something
  other than UTF-8/-16 the exception is raised;
- otherwise if file starts with regular "0" and " " ASCII characters the
  header is read using ANSEL encoding until ``CHAR`` record is met, after
  that reading switches to the encoding specified in that record;
- decoding errors are handled according to the mode specified when opening
  GEDCOM file, it can be one of standard error handling schemes defined in
  ``codecs`` module. This scheme applies to to both header (before ``CHAR``
  record) and regular content.


.. _ANSEL: https://en.wikipedia.org/wiki/ANSEL
.. _BOM: https://en.wikipedia.org/wiki/Byte_order_mark
