from typing import Generator
import peewee
from unittest.mock import patch, MagicMock
from app.project import Project, ProjectDataset, ProjectMember, ProjectModel, NewProject, UpdatedProject
import app.project as project
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
        "id": 1,
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
    assert len(proj.datasets) == 4 # the parent dataset, the supplemental resources, and the two child datasets
    assert ProjectModel.select().count() == 1
    assert ProjectDataset.select().count() == 1
    assert ProjectMember.select().count() == 1

def test_update_project_no_changes():
    proj = Project(**PROJECT)
    proj.save()
    proj_again = Project(**PROJECT)
    assert type(proj_again) == UpdatedProject
    assert proj_again.old_dir_name is None
    assert proj_again.new_datasets is None
    assert proj_again.dirs_to_remove is None
    assert proj_again.new_members is None
    assert proj_again.members_to_remove is None

def test_update_project_name():
    proj = Project(**PROJECT)
    proj.save()
    PROJECT['name'] = 'updated name'
    proj_updated = Project(**PROJECT)
    assert proj_updated.old_dir_name == proj.dir_name
    assert proj_updated.dir_name != proj.dir_name

def test_update_project_add_dataset():
    proj = Project(**PROJECT)
    proj.save()
    new_dataset = copy.deepcopy(PROJECT['datasets'][0])
    new_dataset['uuid'] = 'new uuid'
    PROJECT['datasets'].append(new_dataset)
    proj_updated = Project(**PROJECT)
    assert 'new uuid' in [ds.id for ds in proj_updated.new_datasets if hasattr(ds, 'id')]

def test_update_project_remove_dataset():
    proj = Project(**PROJECT)
    proj.save()
    PROJECT['datasets'].pop()
    proj_updated = Project(**PROJECT)
    proj_updated.save()
    assert len(proj_updated.dirs_to_remove) == 1
    assert proj_updated._datasets_to_remove
    assert ProjectDataset.select().count() == 0

@patch('app.project.logger')
def test_invalid_dataset_xml(mock_logger):
    PROJECT['datasets'][0]['path'] = 'invalid path'
    proj = Project(**PROJECT)
    proj.save()
    mock_logger.error.assert_called_once()
  
DS_1 = {'project_id':1, 'dataset_id':'a', 'staging_dir':'dir1'}
DS_2 = {'project_id':1, 'dataset_id':'b', 'staging_dir':'dir2'}

def test_get_effects():
    '''Demostrate what should happen when a dataset is added to a project
    but already belongs to another project.
    '''
    ProjectDataset.insert(**DS_1).execute()
    ProjectDataset.insert(**DS_2).execute()
    ProjectModel.insert(id=1, name='project name').execute()
    ProjectModel.insert(id=2, name='project name').execute()

    effects = project._get_effects(['a'])
    project_update = next(effects)
    assert next(effects, None) is None
    assert project_update.id == str(DS_1['project_id'])
    assert project_update._datasets_to_remove == [DS_1['dataset_id']]
    assert project_update.dirs_to_remove == [DS_1['staging_dir']]

    effects = project._get_effects(['a', 'b'])
    update_1 = next(effects)
    assert next(effects, None) is None
    assert update_1._datasets_to_remove == [DS_1['dataset_id'], DS_2['dataset_id']]

PROJECT_1 = {
  'id':1,
  'name':'project name',
  'datasets':[
    {
      'id': 1,
      'name': 'dataset name',
      'uuid': 'a',
      'path': TOMATO_PARENT
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

def test_steal_datasets():
    '''
    Test that:
    - a project can steal datasets from another project
    - stealing datasets removes the ProjectDataset rows
    '''
    # create a project with two datasets
    proj_1 = Project(**PROJECT_1)
    proj_1.save()
    # create another project with the same dataset (steal it)
    PROJECT_1['id'] = 2
    proj_2 = Project(**PROJECT_1)
    update = next(proj_2.effects)
    assert len(update._datasets_to_remove) == 1
    update.save()
    assert ProjectDataset.select().count() == 0
    proj_2.save()
    assert ProjectDataset.select().where(ProjectDataset.project_id == 2).count() == 1
    # steal the dataset back again
    PROJECT_1['id'] = 1
    update_proj_1 = Project(**PROJECT_1)
    update = next(update_proj_1.effects)
    assert len(update._datasets_to_remove) == 1
    update.save()
    assert ProjectDataset.select().count() == 0
    update_proj_1.save()
    assert ProjectDataset.select().where(ProjectDataset.project_id == 1).count() == 1