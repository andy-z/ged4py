=======
History
=======

0.4.0 (2020-10-09)
------------------

* Python3 goodies, use enum classes for enums

0.3.2 (2020-10-04)
------------------

* Use numpydoc style for docstrings, add extension to Sphinx
* Drop Python2 compatibility code

0.3.1 (2020-09-28)
------------------

* Use github actions instead of Travis CI

0.3.0 (2020-09-28)
------------------

* Drop Python2 support
* Python3 supported versions are 3.6 - 3.8

0.2.4 (2020-08-30)
------------------

* Extend dialect detection for new genery.com SOUR format

0.2.3 (2020-08-29)
------------------

* Disable hashing for Record types
* Add hash method for DateValue and CalendarDate classes
* Improve ordering of DateValue instances

0.2.2 (2020-08-16)
------------------

* Fix parsing of DATE records with leading blanks

0.2.1 (2020-08-15)
------------------

* Extend documentation with examples
* Extend docstrings for few classes

0.2.0 (2020-07-05)
------------------
* Improve support for GEDCOM date types

0.1.13 (2020-04-15)
-------------------

* Add support for MacOS line breaks (single CR character)

0.1.12 (2020-03-01)
-------------------

* Add support for a bunch of illegal encodings (thanks @Tuisto59 for report).

0.1.11 (2019-01-06)
-------------------

* Improve support for ANSEL encoded documents that use combining characters.

0.1.10 (2018-10-17)
-------------------

* Add protection for empty DATE fields.

0.1.9 (2018-05-17)
------------------

* Improve exception messages, convert bytes to string

0.1.8 (2018-05-16)
------------------

* Add simple integrity checks to parser

0.1.7 (2018-04-23)
------------------

* Fix for DateValue comparison, few small improvements

0.1.6 (2018-04-02)
------------------

* Improve handling of non-standard dates, any date string that cannot
  be parsed according to GEDCOM syntax is assumed to be a "Date phrase"

0.1.5 (2018-03-25)
------------------

* Fix for exception due to empty NAME record

0.1.4 (2018-01-31)
------------------

* Improve name parsing for ALTREE dialect

0.1.3 (2018-01-16)
------------------

* improve Py3 compatibility

0.1.2 (2017-11-26)
------------------

* Get rid of name formatting options, too complicated for this package.
* Describe name parsing for different dialects.

0.1.1 (2017-11-20)
------------------

* Fix for missing modules.

0.1.0 (2017-07-17)
------------------

* First release on PyPI.
