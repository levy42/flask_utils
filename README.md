### Flask Utils
--------------------

#### ManyToManyProxyMixin

For all many to many relations adds "<relation_name>_ids" proxy property,
this is useful when you need to pass only a set of IDs instead of objects.

### FlaskSQLAlchemyFixtures
Flask extension that adds cli commands for fixture management to your application:
    - dump-fixture(sqlalchemy_model_class_path)
    - load-fixture(json_file_path)

Config: 

| FIXTURES_DIR | path to directory where fixtures will be created | ./fixtures |
|--------------|--------------------------------------------------|------------|
    
Example: 
    
    flask dump-fixture myapp.models.User
    flask load-fixtures <fixture_dir>/user.json
    
    
####  Methods:
- model_to_dict: converts sqlalchemy model to python dictionary