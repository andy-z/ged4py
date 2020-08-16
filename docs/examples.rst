========
Examples
========

This page collects several simple code examples which use :py:mod:`ged4py`.


Example 1
---------

Trivial example of opening the file, iterating over INDI records (which
produces :py:class:`~ged4py.model.Individual` instances) and printing basic
information for each person. :py:meth:`~ged4py.model.Name.format` method is
used to produce printable representation of a name, though this is only one of
possible ways to format names. Method
:py:meth:`~ged4py.model.Record.sub_tag_value` is used to access the values of
subordinate tags of the record, it can follow many levels of tags.

.. literalinclude:: example_code/example1.py


Example 2
---------

This example iterates over FAM records in the file which represent family
structure. FAM records do not have special record type so they produce generic
:py:class:`~ged4py.model.Record` instances. This example shows the use of
:py:meth:`~ged4py.model.Record.sub_tag` method which can dereference pointer
records contained in FAM records to retrieve corresponding INDI records.

.. literalinclude:: example_code/example2.py


Example 3
---------

This example shows how to specialize date formatting. Date representation in
different calendars is a very complicated topic and ``ged4py`` cannot solve it
in any general way. Instead it gives clients an option to specialize date
handling in whatever way clients prefer. This is done by implementing
:py:class:`~ged4py.date.DateValueVisitor` interface and passing a visitor
instance to :py:meth:`ged4py.date.DateValue.accept` method. For completeness
one also has to implement :py:class:`~ged4py.calendar.CalendarDateVisitor` to
format or do anything else to the instances of
:py:class:`~ged4py.calendar.CalendarDate`, this is not shown in the example.

.. literalinclude:: example_code/example3.py
