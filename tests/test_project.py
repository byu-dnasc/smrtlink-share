from app.smrtlink import _dict_to_project
from app.project import Project, ProjectDataset, Dataset
import json
import pytest

@pytest.fixture()
def project_dicts_f():
    with open('tests/projects.json') as f:
        return json.load(f)

def test_project(project_dicts_f):
    proj = _dict_to_project(project_dicts_f[0])
    assert Project.select().count() == 1
    assert ProjectDataset.select().count() == 1
    assert Dataset.select().count() == 1
    assert len(proj.datasets) == 1

def test_update_project_no_changes(project_dicts_f):
    proj = _dict_to_project(project_dicts_f[0])
    proj_again = _dict_to_project(project_dicts_f[0])
    assert not proj_again.updates