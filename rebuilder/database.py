import logging
from datetime import datetime

from peewee import *

# logger = logging.getLogger("peewee")
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())

db = SqliteDatabase("database.db")


class BaseModel(Model):
    class Meta:
        database = db


class Origins(BaseModel):
    name = CharField(unique=True)
    alias = CharField(unique=True)
    description = TextField(default="")
    uri = CharField()
    website = CharField(default="")
    timestamp = DateTimeField(default=datetime(1970, 1, 1))


class Suites(BaseModel):
    name = CharField(unique=True)
    origin = ForeignKeyField(Origins, backref="suites")


class Components(BaseModel):
    name = CharField(unique=True)
    suite = ForeignKeyField(Suites, backref="components")


class Storages(BaseModel):
    uri = CharField(primary_key=True)


class Sources(BaseModel):
    name = CharField()
    version = CharField()
    component = ForeignKeyField(Components, backref="sources")
    target = CharField()
    cpe = CharField(null=True)

    class Meta:
        indexes = ((("name", "version", "component", "target"), True),)


class Statues(BaseModel):
    name = CharField(primary_key=True)


class Artifacts(BaseModel):
    buildlog_uri = CharField(default="")
    diffoscope_html_uri = CharField(default="")
    diffoscope_json_uri = CharField(default="")
    binary_uri = CharField(default="")


class Rebuilders(BaseModel):
    name = CharField(unique=True)
    maintainer = CharField()
    contact = CharField()
    uri = CharField()
    pubkey_pgp = CharField(default="")
    pubkey_signify = CharField(default="")
    results_method = CharField(default="")
    artifact_storage = BooleanField(default=False)
    timestamp = DateTimeField(default=datetime(1970, 1, 1))


class Results(BaseModel):
    source = ForeignKeyField(Sources, backref="results")
    rebuilder = ForeignKeyField(Rebuilders, backref="results")
    status = ForeignKeyField(Statues, backref="results")
    tested_version = CharField()
    build_date = DateTimeField()
    build_duration = IntegerField(default=0)
    artifacts = ForeignKeyField(Artifacts)
    build_env = TextField(default="")
    storage_uri = ForeignKeyField(Storages)

    class Meta:
        primary_key = CompositeKey(
            "source", "tested_version", "rebuilder", "build_date"
        )


def init_db():
    db.create_tables(
        [
            Origins,
            Suites,
            Storages,
            Components,
            Sources,
            Statues,
            Rebuilders,
            Artifacts,
            Results,
        ]
    )

    Statues.insert_many(
        [
            {"name": "reproducible"},
            {"name": "unreproducible"},
            {"name": "buildfail"},
            {"name": "notfound"},
            {"name": "timeout"},
            {"name": "blocked"},
            {"name": "untested"},
            {"name": "depwait"},
        ]
    ).on_conflict_ignore().execute()
