from piccolo.columns import ForeignKey, Varchar
from piccolo.table import Table, sort_table_classes


class Thing(Table):
    name = Varchar(length=50)


class OtherThing(Table):
    name = Varchar(length=50)


class OwnedBy(Table):
    thing = ForeignKey(references=Thing)
    other_thing = ForeignKey(references=OtherThing)


TABLES = sort_table_classes([Thing, OtherThing, OwnedBy])
