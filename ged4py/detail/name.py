"""Internal module for parsing names in gedcom format."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..model import Record


def split_name(name: str) -> tuple[str, str, str]:
    """Extract pieces of name from full name string.

    Parameters
    ----------
    name : `str`
        Full name string.

    Returns
    -------
    name : `tuple`
        3-tuple `(given1, surname, given2)`, `surname` or `given` will
        be empty strings if they are not present in full string.

    Notes
    -----
    Full name can have one of these formats::

        <NAME_TEXT> |
        /<NAME_TEXT>/ |
        <NAME_TEXT> /<NAME_TEXT>/ |
        /<NAME_TEXT>/ <NAME_TEXT> |
        <NAME_TEXT> /<NAME_TEXT>/ <NAME_TEXT>

    <NAME_TEXT> can include almost anything excluding commas, numbers,
    special characters (though some test files use numbers for the names).
    Text between slashes is considered a surname, outside slashes - given
    name.

    This method splits full name into pieces at slashes, e.g.::

        "First /Last/" -> ("First", "Last", "")
        "/Last/ First" -> ("", "Last", "First")
        "First /Last/ Jr." -> ("First", "Last", "Jr.")
        "First Jr." -> ("First Jr.", "", "")

    """
    given1, _, rem = name.partition("/")
    surname, _, given2 = rem.partition("/")
    return given1.strip(), surname.strip(), given2.strip()


def parse_name_altree(record: Record) -> tuple[str, str, str] | tuple[str, str, str, str]:
    """Parse NAME structure assuming ALTREE dialect.

    Parameters
    ----------
    record : `ged4py.model.Record`
        NAME record.

    Returns
    -------
    parsed_name : `tuple`
        Tuple with 3 or 4 elements, first three elements of tuple are
        the same as returned from `split_name` method, fourth element
        (if present) denotes maiden name.

    Notes
    -----
    In ALTREE dialect maiden name (if present) is saved as SURN sub-record
    and is also appended to family name in parens. Given name is saved in
    GIVN sub-record. Few examples:

    No maiden name::

        1 NAME John /Smith/
        2 GIVN John

    With maiden name::

        1 NAME Jane /Smith (Ivanova)/
        2 GIVN Jane
        2 SURN Ivanova

    No maiden name::

        1 NAME Mers /Daimler (-Benz)/
        2 GIVN Mers

    Because family name can also contain parens it's not enough to parse
    family name and guess maiden name from it, we also have to check for
    SURN record.

    ALTREE also replaces empty names with question mark, we undo that too.
    """
    assert isinstance(record.value, str)
    name_tuple: tuple[str, str, str] | tuple[str, str, str, str]
    name_tuple = split_name(record.value)
    if name_tuple[1] == "?":
        name_tuple = (name_tuple[0], "", name_tuple[2])
    maiden = record.sub_tag_value("SURN")
    if maiden:
        # strip "(maiden)" from family name
        ending = "(" + maiden + ")"
        surname = name_tuple[1]
        if surname.endswith(ending):
            surname = surname[: -len(ending)].rstrip()
            if surname == "?":
                surname = ""
        name_tuple = (name_tuple[0], surname, name_tuple[2], maiden)
    return name_tuple


def parse_name_myher(record: Record) -> tuple[str, str, str] | tuple[str, str, str, str]:
    """Parse NAME structure assuming MYHERITAGE dialect.

    Parameters
    ----------
    record : `ged4py.model.Record`
        NAME record.

    Returns
    -------
    parsed_name : `tuple`
        Tuple with 3 or 4 elements, first three elements of tuple are
        the same as returned from `split_name` method, fourth element
        (if present) denotes maiden name.

    Notes
    -----
    In MYHERITAGE dialect married name (if present) is saved as _MARNM
    sub-record. Maiden name is stored in SURN record. Few examples:

    No maiden name::

        1 NAME John /Smith/
        2 GIVN John
        2 SURN Smith

    With maiden name::

        1 NAME Jane /Ivanova/
        2 GIVN Jane
        2 SURN Ivanova
        2 _MARNM Smith

    No maiden name::

        1 NAME Mers /Daimler (-Benz)/
        2 GIVN Mers
        2 SURN Daimler (-Benz)


    """
    assert isinstance(record.value, str)
    name_tuple: tuple[str, str, str] | tuple[str, str, str, str]
    name_tuple = split_name(record.value)
    married = record.sub_tag_value("_MARNM")
    if married:
        maiden = name_tuple[1]
        name_tuple = (name_tuple[0], married, name_tuple[2], maiden)
    return name_tuple


def parse_name_ancestris(record: Record) -> tuple[str, str, str]:
    """Parse NAME structure assuming ANCESTRIS dialect.

    As far as I can tell Ancestris does not have any standard convention for
    representing maiden or married names. Best we can do in this situation is
    to use NAME record value and ignore any other fields.

    Parameters
    ----------
    record : `ged4py.model.Record`
        NAME record.

    Returns
    -------
    parsed_name : `tuple`
        Tuple with 3 or 4 elements, first three elements of tuple are
        the same as returned from `split_name` method, fourth element
        (if present) denotes maiden name.
    """
    assert isinstance(record.value, str)
    name_tuple = split_name(record.value)
    return name_tuple
