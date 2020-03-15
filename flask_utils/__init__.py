from datetime import datetime, date
import json
import importlib
from uuid import UUID
import os

import click
from flask import Flask
from sqlalchemy import inspect
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


def model_from_dict(model_class, data):
    return model_class(**data)


def load_model_fixtures(db, path, deserialize=model_from_dict):
    """Loads the given fixtures into the database.
    """
    fixtures = json.load(open(path))

    for fixture in fixtures:
        if 'model' in fixture:
            module_name, class_name = fixture['model'].rsplit('.', 1)
            module = importlib.import_module(module_name)
            model = getattr(module, class_name)
            for fields in fixture['records']:
                obj = deserialize(model, fields)
                db.session.add(obj)
            db.session.commit()
        else:
            raise ValueError(
                "Fixture missing a 'model' field: {0}".format(json.dumps(fixture)))


def dump_model_fixture(db, model_path, limit=10000, fixtures_dir='fixtures',
                       serialize=model_to_dict):
    module_name, class_name = model_path.rsplit('.', 1)
    query = db.session.query(importlib.import_module(module_name))
    records = [serialize(i) for i in query.limit(limit).all()]
    data = [{'model': model_path, 'records': records}]

    fixture_name = stringcase.snakecase(class_name)
    with open(os.path.join(fixtures_dir, fixture_name + '.json'), 'w') as f:
        json.dump(data, f, default=extended_json_encoder)


class FlaskSQLAlchemyFixtures:
    def __init__(self, app: Flask = None, db=None, serializer=model_to_dict,
                 deserializer=model_from_dict):
        self.app = app
        self.db = db
        self.fixtures_dir = None
        self.init_app(app, db)
        self.serializer = serializer
        self.deserializer = deserializer

    def init_app(self, app, db):
        self.app = app
        self.db = db
        self.fixtures_dir = app.config['FIXTURES_DIR']

        @app.cli.command()
        @click.argument('path')
        def load_fixture(path):
            load_model_fixtures(db, path, deserialize=self.deserializer)

        @app.cli.command()
        @click.argument('model_path')
        @click.option('--limit', default=1000)
        def dump_fixture(model_path, limit):
            dump_model_fixture(db, model_path, limit=limit, fixtures_dir=self.fixtures_dir,
                               serialize=self.serializer)

        @app.cli.command()
        def create_db():
            db.create_all()
