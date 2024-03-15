import json
import pytest
import peewee as pw
from project import Project, dict_to_project
import smrtlink

def get_project_dicts():
    with open('tests/projects.json') as f:
        return json.load(f)

@pytest.fixture()
def projects_f():
    '''Fixture may be unnecessary as long as the data is not modified in the test.'''
    return [dict_to_project(p_dict) for p_dict in get_project_dicts()]

@pytest.fixture()
def db_projects(request, projects_f):
    marker = request.node.get_closest_marker('db_offset')
    index = -1 if marker else len(projects_f)
    return projects_f[0:index]
    
@pytest.fixture(autouse=True)
def db(db_projects):
    '''Adapt functionality in project.init_db() for using an in-memory database'''
    db = pw.SqliteDatabase(':memory:')
    Project.bind(db)
    db.connect() # open a connection so that the in-memory database stays alive
    db.create_tables([Project], safe=True)
    for project in db_projects:
        project.save(force_insert=True) # override query type UPDATE with INSERT
    yield
    db.close() # close the final connection to destroy the database

@pytest.fixture(autouse=True)
def sl():
    class SmrtLinkTestClient:
        projects = get_project_dicts()
        def get_project_dict(self, id):
            return self.projects[id]
        def get_project_ids(self):
            return self.projects
    smrtlink.DnascSmrtLinkClient._instance = SmrtLinkTestClient()

@pytest.mark.db_offset()
def test_offset(projects_f):
    assert (Project.select().count() + 1) == len(projects_f)

def test_sl_test_client(projects_f):
    assert len(smrtlink.get_client().get_project_ids()) == len(projects_f)
