import json
import pytest
import peewee as pw
import project
import smrtlink

pytestmark = pytest.mark.usefixtures('sl') # tests in this file use the SMRT Link "test client"

def get_project_dicts():
    with open('tests/projects.json') as f:
        return json.load(f)

@pytest.fixture()
def projects_f():
    '''
    Fixture to provide access to a set of project dictionaries.
    Using a fixture prevents contamination between tests in the
    case that project data gets modified.
    '''
    return [project.dict_to_project(p_dict) for p_dict in get_project_dicts()]

@pytest.fixture()
def db_projects(request, projects_f):
    '''
    Fixture to get a subset of projects to populate database. 
    The subset (default to all projects) is controlled by the
    db_offset marker.
    '''
    last_project_index = len(projects_f) # default to no offset
    marker = request.node.get_closest_marker('db_offset')
    if marker:
        offset_index = -1 # use default offset (-1)
        if len(marker.args) > 0:
            offset_index = -abs(marker.args[0]) # offset is arg[0]
        last_project_index = offset_index
    return projects_f[0:last_project_index]
    
@pytest.fixture(autouse=True)
def db(db_projects):
    '''
    Adapt functionality in project.init_db() for using an in-memory database.
    Database content is determined by the db_projects fixture.
    '''
    db = pw.SqliteDatabase(':memory:')
    project.Project.bind(db)
    db.connect() # open a connection so that the in-memory database stays alive
    db.create_tables([project.Project], safe=True)
    for p in db_projects:
        p.save(force_insert=True) # override query type UPDATE with INSERT
    yield
    db.close() # close the final connection to destroy the database

@pytest.mark.db_offset()
def test_offset(projects_f):
    num_db_projects = project.Project.select().count()
    assert num_db_projects == len(projects_f) - 1

def test_sl_test_client(projects_f):
    assert len(smrtlink.get_client().get_project_ids()) == len(projects_f)

def test_get():
    assert project.get(1).name == 'General Project'
    assert project.get(999) is None

def test_get_new_none():
    '''
    If there are no new projects, i.e. if the database is in sync with
    SMRT Link, then get_new() should return None.
    '''
    assert project.get_new() is None

@pytest.mark.db_offset()
def test_get_new(projects_f):
    '''
    If there is one new project, i.e. if offset is one, then get_new()
    should return the latest project from SMRT Link, which is the same
    as the last project in the projects_f fixture.
    '''
    assert project.get_new().name == projects_f[-1].name

@pytest.mark.db_offset(2)
def test_get_new_out_of_sync():
    with pytest.raises(project.OutOfSyncError):
        project.get_new()