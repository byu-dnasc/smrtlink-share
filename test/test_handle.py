import unittest.mock
import pytest

import test.data
import app.handle
import app.state

STAGE = 1
UNSTAGE = 2
TRACK_JOB = 3
ADD_MEMBER = 4
MEMBER_EXISTS = 5
PREVIOUS_MEMBERS = 6
DATASET_BY_UUID = 7
ADD_DATASET = 8
PREVIOUS_DATASETS = 9
CREATE_PERMISSION = 10
REMOVE_PERMISSIONS = 11
REMOVE_PERMISSION = 12
GET_ANALYSES = 13
REMOVE_MEMBER = 14
REMOVE_DATASET = 15
UPDATE_DATASET_PROJECT = 16

from unittest.mock import patch
patchers = {
    STAGE: patch('app.filesystem.stage', return_value=True),
    UNSTAGE: patch('app.filesystem.remove', return_value=True),
    TRACK_JOB: patch('app.job.track'),
    ADD_MEMBER: patch('app.state.ProjectMember.add'),
    MEMBER_EXISTS: patch('app.state.ProjectMember.exists', return_value=False),
    PREVIOUS_MEMBERS: patch('app.state.ProjectMember.get_previous_members', return_value=[]),
    DATASET_BY_UUID: patch('app.state.Dataset.where_dataset_uuid', return_value=None),
    ADD_DATASET: patch('app.state.Dataset.add'),
    PREVIOUS_DATASETS: patch('app.state.Dataset.get_previous_datasets', return_value=[]),
    CREATE_PERMISSION: patch('app.globus.create_permission'),
    REMOVE_PERMISSIONS: patch('app.globus.remove_permissions'),
    REMOVE_PERMISSION: patch('app.globus.remove_permission'),
    GET_ANALYSES: patch('app.job.get_analyses', return_value=([], [])),
    REMOVE_MEMBER: patch('app.state.ProjectMember.delete_instance'),
    REMOVE_DATASET: patch('app.state.Dataset.delete_instance'),
    UPDATE_DATASET_PROJECT: patch('app.state.Dataset.update_project_id'),
}

@pytest.fixture()
def mock():
    mocks = {i: patcher.start() for i, patcher in patchers.items()}
    yield mocks
    unittest.mock.patch.stopall()

@pytest.fixture
def dataset():
    return [None, test.data.DATASET_1, test.data.DATASET_2, 
            test.data.DATASET_3, test.data.DATASET_4, test.data.DATASET_5]

@pytest.fixture
def member():
    return [None, test.data.MEMBER_1, test.data.MEMBER_2]

def test_empty_project(mock: dict[int, unittest.mock.MagicMock]):
    app.handle._handle_project(1, [], [])
    for i in (STAGE, UNSTAGE, ADD_MEMBER, REMOVE_MEMBER, ADD_DATASET, REMOVE_DATASET, 
              CREATE_PERMISSION, REMOVE_PERMISSIONS, REMOVE_PERMISSION):
        mock[i].assert_not_called()

def test_new_dataset(mock: dict[int, unittest.mock.MagicMock], dataset):
    app.handle._handle_project(1, [dataset[1]], [])
    mock[ADD_DATASET].assert_called_once()
    mock[STAGE].assert_called()

def test_reassigned_dataset(mock: dict[int, unittest.mock.MagicMock], dataset, member):
    # simulate prior app state with respect to 'dataset 1'
    mock[DATASET_BY_UUID].return_value = app.state.Dataset(uuid=dataset[1]['uuid'],
                                                         project_id=1,
                                                         dir_path='whatever')
    # reassign 'dataset 1' to project 2
    NEW_PROJECT_ID = 2
    app.handle._handle_project(NEW_PROJECT_ID, [dataset[1]], [])
    mock[UPDATE_DATASET_PROJECT].assert_called_once_with(NEW_PROJECT_ID)
    mock[ADD_DATASET].assert_not_called()
    mock[STAGE].assert_not_called()
