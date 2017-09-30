"""Internal module for parsing names in gedcom format.
"""

from __future__ import print_function, absolute_import, division


def split_name(name):
    """Extracts pieces of name from full name string.

    Full name can have one of these formats:
        <NAME_TEXT> |
        /<NAME_TEXT>/ |
        <NAME_TEXT> /<NAME_TEXT>/ |
        /<NAME_TEXT>/ <NAME_TEXT> |
        <NAME_TEXT> /<NAME_TEXT>/ <NAME_TEXT>

    <NAME_TEXT> can include almost anything excluding commas, numbers,
    special characters (though some test files use numbers for the names).
    Text between slashes is considered a surname, outside slashes - given
    name.

    This method splits full name into pieces at slashes, e.g.:

        "First /Last/" -> ("First", "Last", "")
        "/Last/ First" -> ("", "Last", "First")
        "First /Last/ Jr." -> ("First", "Last", "Jr.")
        "First Jr." -> ("First Jr.", "", "")

    :param str name: Full name string.
    :return: 2-tuple `(given1, surname, given2)`, `surname` or `given` will
        be empty strings if they are not present in full string.
    """
    given1, _, rem = name.partition("/")
    surname, _, given2 = rem.partition("/")
    return given1.strip(), surname.strip(), given2.strip()
