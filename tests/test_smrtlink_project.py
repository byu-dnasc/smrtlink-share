import pytest
import json
from app.project import Project
import app.smrtlink as smrtlink

@pytest.fixture()
def project_dicts_f():
    '''Fixture to prevent any possible contamination between tests.'''
    with open('tests/projects.json') as f:
        return json.load(f)

class SmrtLinkTestClient:
    '''Mimic DnascSmrtLinkClient for more convenience in testing.'''
    def __init__(self, project_dicts):
        self.project_dicts = project_dicts
    def get_project_dict(self, id):
        zero_based_id = id - 1
        if zero_based_id < 0 or zero_based_id >= len(self.project_dicts):
            return None
        return self.project_dicts[zero_based_id]
    def get_project_ids(self):
        return [p_d['id'] for p_d in self.project_dicts]

@pytest.fixture(autouse=True)
def install_test_client(project_dicts_f):
    smrtlink.CLIENT = SmrtLinkTestClient(project_dicts_f)

@pytest.fixture(autouse=True)
def load_db(request, project_dicts_f):
    '''
    Fixture to load the database with a subset of the projects
    from SMRT Link. The subset (default to all projects) is 
    controlled by the db_offset marker.
    '''
    last_project_index = len(project_dicts_f) # default to no offset
    marker = request.node.get_closest_marker('db_offset')
    if marker:
        offset_index = -1 # use default offset (-1)
        if len(marker.args) > 0:
            offset_index = -abs(marker.args[0]) # offset is arg[0]
        last_project_index = offset_index
    # load data into the database by instantiating Project objects
    for dct in project_dicts_f[0:last_project_index]: Project(**dct) 
 
@pytest.mark.db_offset()
def test_offset(project_dicts_f):
    num_db_projects = Project.select().count()
    assert num_db_projects == len(project_dicts_f) - 1

def test_get_project():
    assert smrtlink.get_project(1).name == 'General Project'
    assert smrtlink.get_project(999) is None

def test_get_new_none():
    '''
    If there are no new projects, i.e. if the database is in sync with
    SMRT Link, then get_new() should return None.
    '''
    assert smrtlink.get_new_project() is None

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

