from datetime import datetime, date
import json
import importlib
from uuid import UUID
import os

import click
from flask import Flask
from sqlalchemy import inspect, Table
from sqlalchemy.orm.relationships import MANYTOMANY
import stringcase


class ManyToManyProxyMixin:
    @classmethod
    def __declare_last__(cls):
        for name, rel in inspect(cls).relationships.items():
            if rel.direction == MANYTOMANY:
                def get_property(name, rel):
                    def getter(self):
                        return [i.id for i in getattr(self, name)]

                    def setter(self, val):
                        setattr(self, name, [
                            rel.mapper.entity.query.get(i) for i in val
                        ])

                    return property(
                        fget=getter,
                        fset=setter
                    )

            setattr(cls, name + '_ids', get_property(name, rel))


def extended_json_encoder(x):
    if isinstance(x, (datetime, date)):
        return x.isoformat()
    if isinstance(x, UUID):
        return str(x)


def model_to_dict(model):
    return {k: v for k, v in model.__dict__.items() if not k.startswith('_')}


def load_model_fixtures(db, fixtures):
    """Loads the given fixtures into the database.
    """
    conn = db.engine.connect()
    metadata = db.metadata

    for fixture in fixtures:
        if 'model' in fixture:
            module_name, class_name = fixture['model'].rsplit('.', 1)
            module = importlib.import_module(module_name)
            model = getattr(module, class_name)
            for fields in fixture['records']:
                obj = model(**fields)
                db.session.add(obj)
            db.session.commit()
        elif 'table' in fixture:
            table = Table(fixture['table'], metadata)
            conn.execute(table.insert(), fixture['records'])
        else:
            raise ValueError(
                "Fixture missing a 'model' or 'table' field: {0}".format(json.dumps(fixture)))


def dump_model_fixture(db, model_path, limit=10000, fixtures_dir='fixtures'):
    module_name, class_name = model_path.rsplit('.', 1)
    query = db.session.query(importlib.import_module(module_name))
    records = [model_to_dict(i) for i in query.limit(limit).all()]
    data = [{'model': model_path, 'records': records}]

    fixture_name = stringcase.snakecase(class_name)
    with open(os.path.join(fixtures_dir, fixture_name + '.json'), 'w') as f:
        json.dump(data, f, default=extended_json_encoder)


class FlaskSQLAlchemyFixtures:
    def __init__(self, app: Flask = None, db=None):
        self.app = app
        self.db = db
        self.fixtures_dir = None
        self.init_app(app, db)

    def init_app(self, app, db):
        self.app = app
        self.db = db
        self.fixtures_dir = app.config['FIXTURES_DIR']

        @app.cli.command()
        @click.argument('name')
        def load_fixture(path):
            load_model_fixtures(db, path)

        @app.cli.command()
        @click.argument('model_path')
        @click.option('--limit', default=1000)
        def dump_fixture(model_path, limit):
            dump_model_fixture(db, model_path, limit=limit, fixtures_dir=self.fixtures_dir)

        @app.cli.command()
        def create_db():
            db.create_all()
