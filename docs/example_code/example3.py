import sys

from ged4py.date import DateValueVisitor
from ged4py.parser import GedcomReader


class DateFormatter(DateValueVisitor):
    """Visitor class that produces string representation of dates."""

    def visitSimple(self, date):
        return f"{date.date}"

    def visitPeriod(self, date):
        return f"from {date.date1} to {date.date2}"

    def visitFrom(self, date):
        return f"from {date.date}"

    def visitTo(self, date):
        return f"to {date.date}"

    def visitRange(self, date):
        return f"between {date.date1} and {date.date2}"

    def visitBefore(self, date):
        return f"before {date.date}"

    def visitAfter(self, date):
        return f"after {date.date}"

    def visitAbout(self, date):
        return f"about {date.date}"

    def visitCalculated(self, date):
        return f"calculated {date.date}"

    def visitEstimated(self, date):
        return f"estimated {date.date}"

    def visitInterpreted(self, date):
        return f"interpreted {date.date} ({date.phrase})"

    def visitPhrase(self, date):
        return f"({date.phrase})"


format_visitor = DateFormatter()

with GedcomReader(sys.argv[1]) as parser:
    # iterate over each INDI record in a file
    for i, indi in enumerate(parser.records0("INDI")):
        print(f"{i}: {indi.name.format()}")

        # get all possible event types and print their dates,
        # full list of events is longer, this is only an example
        events = indi.sub_tags("BIRT", "CHR", "DEAT", "BURI", "ADOP", "EVEN")
        for event in events:
            date = event.sub_tag_value("DATE")
            # Some event types like generic EVEN can define TYPE tag
            event_type = event.sub_tag_value("TYPE")
            # pass a visitor to format the date
            if date:
                date_str = date.accept(format_visitor)
            else:
                date_str = "N/A"
            print(f"    event: {event.tag} date: {date_str} type: {event_type}")
