import sys

from ged4py.parser import GedcomReader

with GedcomReader(sys.argv[1]) as parser:
    # iterate over each FAM record in a file
    for i, fam in enumerate(parser.records0("FAM")):
        print(f"{i}:")

        # Get records for spouses, FAM record contains pointers to INDI
        # records but sub_tag knows how to follow the pointers and return
        # the referenced records instead.
        husband, wife = fam.sub_tag("HUSB"), fam.sub_tag("WIFE")
        if husband:
            print(f"    husband: {husband.name.format()}")
        if wife:
            print(f"    wife: {wife.name.format()}")

        # Get _value_ of the MARR/DATE tag
        marr_date = fam.sub_tag_value("MARR/DATE")
        if marr_date:
            print(f"    marriage date: {marr_date}")

        # access all CHIL records, sub_tags method returns list, possibly empty
        children = fam.sub_tags("CHIL")
        for child in children:
            # print name and date of birth
            print(f"    child: {child.name.format()}")
            birth_date = child.sub_tag_value("BIRT/DATE")
            if birth_date:
                print(f"        birth date: {birth_date}")
