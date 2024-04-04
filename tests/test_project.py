import pytest
from tests.conftest import get_project_dicts
from smrtlink import _dict_to_project
import peewee as pw
import project

@pytest.fixture(autouse=True)
def db():
    '''
    Adapt functionality in project.init_db() for using an in-memory database.
    Database content is determined by the db_projects fixture.
    '''
    db = pw.SqliteDatabase(':memory:')
    project.Project.bind(db)
    project.Dataset.bind(db)
    db.connect() # open a connection so that the in-memory database stays alive
    db.create_tables([project.Project, project.Dataset], safe=True)
    yield
    db.close() # close the final connection to destroy the database

def test_project_update_db():
    proj_dicts = get_project_dicts()
    proj = _dict_to_project(proj_dicts[1])
    assert proj
    proj.update_db()
    proj_db = project.Project.get(project.Project.id == proj.id)
    assert proj_db.name == proj.name

def test_project():
    proj_dicts = get_project_dicts()
    proj = _dict_to_project(proj_dicts[1])
    assert proj.updates == []