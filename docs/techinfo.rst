.. highlight:: none

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

See also Tamura Jones' excellent `article`_ summarizing many varieties of
illegal encodings that may be present in GEDCOM files.

.. _ANSEL: https://en.wikipedia.org/wiki/ANSEL
.. _BOM: https://en.wikipedia.org/wiki/Byte_order_mark
.. _article: https://www.tamurajones.net/GEDCOMCharacterEncodings.xhtml

Name representation
-------------------

GEDCOM ``NAME`` record defines a structured format for representing names but
applications are not required to fill that structural information and can
instead present name as a value part or ``NAME`` record in a "custom of
culture" representation. Only requirement for that representation is that
surname should be delimited by slash characters, e.g.::

    0 @I1@ INDI
      1 NAME John /Smith/            -- given name and surname
    0 @I2@ INDI
      1 NAME Joanne                  -- without surname
    0 @I3@ INDI
      1 NAME /Иванов/ Иван Ив.       -- surname and given name
    0 @I4@ INDI
      1 NAME Sir John /Ivanoff/ Jr.  -- with prefix/suffix

Potentially individual can have more than one NAME record which can be
distinguished by TYPE record which can be arbitrary string, GEDCOM does not
define standard or allowed types. Types could be use for example to specify
maiden name or names in previous marriages, e.g.::

    0 @I1@ INDI
      1 NAME Жанна /Иванова/
      1 NAME Jeanne /d'Arc/
        2 TYPE maiden

Couple of application that I know of do not use TYPE records for maiden name
representation instead they chose different ways to encode names. Here is how
individual applications encode names.

Agelong Tree (Genery)
~~~~~~~~~~~~~~~~~~~~~

`Agelong Tree`_ produces single NAME record per individual, I don't think it
is possible to make it to create more than one NAME record. Given name and
and surname are encoded as value in the NAME record, and given name also
appears in GIVN sub-record::

    1 NAME Given Name /Surname/
      2 GIVN Given Name

If person has a maiden name then it is encoded as additional surname enclosed
in parentheses, also SURN sub-record specifies maiden name::

    1 NAME Given Name /Surname (Maiden)/
      2 GIVN Given Name
      2 SURN Maiden

Additionally Agelong tends to represent missing parts of names in GEDCOM file
with question mark (?).

Agelong can also store name suffix and prefix, they are not included into NAME
record value but stored as NPFX and NSFX sub-records::

    1 NAME Given Name /Surname/
      2 NPFX Dr.
      2 GIVN Given Name
      2 NSFX Jr.

MyHeritage
~~~~~~~~~~

`MyHeritage`_ Family Tree Builder can generate more than one NAME record but
I could not find a way to specify TYPE of the created NAME records, likely
all NAME records are created without TYPE which is not too useful.

Given name and and surname are encoded as value in the NAME record and they
also appear in GIVN and SURN sub-records::

    1 NAME Given Name /Surname/
      2 GIVN Given Name
      2 SURN Surname

If name of the person after marriage is different from birth/maiden name
(apparently in MyHeritage this can only happen for female individuals) then
married name is stored in a non-standard sub-record with ``_MARNM`` tag::

    1 NAME Given Name /Maiden/
      2 GIVN Given Name
      2 SURN Maiden
      2 _MARNM Married

MyHeritage can also store name suffix and prefix, and also nickname in
corresponding sub-records, they are not rendered in NAME record value::

    1 NAME Given Name /Surname/
      2 NPFX Dr.
      2 GIVN Given Name
      2 SURN Surname
      2 NSFX Jr.
      2 NICK Professore

MyHeritage can also store few name pieces in NAME sub-records using
non-standard tags such as ``_AKA``, ``_RNAME`` (for religious name),
``_FORMERNAME``, etc.

ged4py behavior
~~~~~~~~~~~~~~~

ged4py tries to determine individual name pieces from all info in GEDCOM
records. Because interpretation of the information depends on the application
which produced GEDCOM file ged4py also has to determine the application name.
Application name (a.k.a. GEDCOM "dialect") is determined from file header and
is stored in a ``dialect`` property of :py:class:`~ged4py.parser.GedcomReader`
class (one of the DIALECT_* constants defined in :py:mod:`ged4py.model`
module). In general naming of individuals can be overly complicated, ged4py
tries to build a simpler model of person naming by determining four pieces of
each individual's name:

- given name, in some cultures it can include middle (or father) name
- first name, ged4py just uses first word (before space) of given name
- last name, for married females who changed their name in marriage ged4py
  assumes this to be a married name
- maiden name, only applies to married females who changed their name in
  marriage

Here is the algorithm that ged4py uses for extracting these pieces:

- for Agelong dialect:

  * only NAME record value is used, sub-records are ignored
  * maiden name is determined from parenthesized portion of surname
  * last name is everything except maiden name in surname
  * given name is value without surname, collects everything before and
    after slashes in NAME value

- for MyHeritage dialect:

  * if ``_MARNM`` sub-record is present then it is used as last name and
    everything between slashes in NAME value is used as maiden name
  * otherwise everything between slashes is used as last name, maiden name
    is empty
  * given name is NAME value without slashes and stuff between slashes

- for other cases ("default" dialect):

  * if there is NAME record with TYPE sub-record equal 'maiden' then use
    surname from that record value as maiden name
  * if there is more than one NAME record choose one without TYPE sub-record
    as "primary" name, or use first NAME record; last name comes from
    primary NAME value between slashes, first name is the  rest of value.

.. _Agelong Tree: https://genery.com
.. _MyHeritage: https://www.myheritage.com
