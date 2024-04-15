from app.smrtlink import _dict_to_project
from app.project import Project, ProjectDataset, ProjectMember
import json
import pytest
import copy

@pytest.fixture()
def project_dicts_f():
    with open('tests/projects.json') as f:
        return json.load(f)

def test_project(project_dicts_f):
    proj = Project(**project_dicts_f[0])
    assert Project.select().count() == 1
    assert ProjectDataset.select().count() == 1
    assert ProjectMember.select().count() == 1
    assert len(proj.datasets) == 1

def test_update_project_no_changes(project_dicts_f):
    p_d = project_dicts_f[0]
    proj = Project(**p_d)
    proj_again = Project(**p_d)
    assert not hasattr(proj_again, 'datasets_to_add')
    assert not hasattr(proj_again, 'datasets_to_remove')
    assert not hasattr(proj_again, 'members_to_add')
    assert not hasattr(proj_again, 'members_to_remove')

def test_update_project_name(project_dicts_f):
    p_d = project_dicts_f[0]
    proj = Project(**p_d)
    p_d['name'] = 'updated name'
    proj_updated = Project(**p_d)
    assert proj_updated.updates == ['name']

def test_update_project_add_dataset(project_dicts_f):
    p_d = project_dicts_f[0]
    proj = Project(**p_d)
    new_dataset = copy.deepcopy(p_d['datasets'][0])
    new_dataset['uuid'] = 'new uuid'
    p_d['datasets'].append(new_dataset)
    proj_updated = Project(**p_d)
    assert proj_updated.updates == ['datasets']
    assert proj_updated.datasets_to_stage == ['new uuid']
    assert not hasattr(proj_updated, 'datasets_to_remove')

def test_update_project_remove_dataset(project_dicts_f):
    p_d = project_dicts_f[0]
    proj = Project(**p_d)
    ds_removed = p_d['datasets'].pop()
    proj_updated = Project(**p_d)
    assert proj_updated.updates == ['datasets']
    assert not hasattr(proj_updated, 'datasets_to_stage')
    assert proj_updated.datasets_to_remove == [ds_removed['uuid']]