import peewee
from app.project import Project, ProjectDataset, ProjectMember, ProjectModel, NewProject, UpdatedProject
import json
import pytest
import os
import copy
from tests.test_dataset import TOMATO_PARENT

@pytest.fixture()
def project_dicts_f():
    with open('tests/projects.json') as f:
        return json.load(f)

PROJECT = {
    "id": 1,
    "name": "Tomato Project",
    "datasets": [
      {
        "name": "Germany tomato 20 and 21-Cell1 (all samples)",
        "numChildren": 2,
        "uuid": "48a71a3e-c97c-43ea-ba41-8c2b31dd32b2",
        "path": TOMATO_PARENT
      }
    ],
    "members": [
      {
        "login": "admin",
        "role": "OWNER"
      },
      {
        "login": "superawesomeuser",
        "role": "CAN_VIEW"
      }
    ]
}

def test_project():
    proj = Project(**PROJECT)
    proj.save()
    assert type(proj) == NewProject
    assert len(proj.datasets) == 3 # the parent dataset in PROJECT and its two child datasets
    assert ProjectModel.select().count() == 1
    assert ProjectDataset.select().count() == 1
    assert ProjectMember.select().count() == 1
    assert pytest.raises(peewee.IntegrityError, proj.save)

def test_update_project_no_changes():
    proj = Project(**PROJECT)
    proj.save()
    proj_again = Project(**PROJECT)
    assert type(proj_again) == UpdatedProject
    assert not hasattr(proj_again, 'old_name')
    assert not hasattr(proj_again, 'datasets_to_add')
    assert not hasattr(proj_again, 'dirs_to_remove')
    assert not hasattr(proj_again, 'members_to_add')
    assert not hasattr(proj_again, 'members_to_remove')

def test_update_project_name():
    proj = Project(**PROJECT)
    proj.save()
    PROJECT['name'] = 'updated name'
    proj_updated = Project(**PROJECT)
    assert hasattr(proj_updated, 'old_name')

def test_update_project_add_dataset():
    proj = Project(**PROJECT)
    proj.save()
    new_dataset = copy.deepcopy(PROJECT['datasets'][0])
    new_dataset['uuid'] = 'new uuid'
    PROJECT['datasets'].append(new_dataset)
    proj_updated = Project(**PROJECT)
    assert hasattr(proj_updated, 'datasets_to_add')
    assert [ds.id for ds in proj_updated.datasets_to_add] == ['new uuid']

def test_update_project_remove_dataset():
    proj = Project(**PROJECT)
    proj.save()
    PROJECT['datasets'].pop()
    proj_updated = Project(**PROJECT)
    assert hasattr(proj_updated, 'dirs_to_remove')
    assert len(proj_updated.dirs_to_remove) == 1
