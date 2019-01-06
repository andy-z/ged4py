=======
History
=======

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
