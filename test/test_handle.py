import unittest.mock
import pytest

import test.data
import app.handle
import app.state

STAGE = 1
UNSTAGE = 2
TRACK_JOB = 3
INSERT_MEMBER = 4
MEMBER_EXISTS = 5
PREVIOUS_MEMBERS = 6
DATASET_BY_UUID = 7
INSERT_DATASET = 8
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
    # functions which modify the state of the app, or interact with external services
    STAGE: patch('app.filesystem.stage', return_value=True),
    UNSTAGE: patch('app.filesystem.remove', return_value=True),
    INSERT_MEMBER: patch('app.state.ProjectMember.insert'),
    INSERT_DATASET: patch('app.state.Dataset.insert'),
    CREATE_PERMISSION: patch('app.globus.create_permission'),
    REMOVE_PERMISSIONS: patch('app.globus.remove_permissions'),
    REMOVE_PERMISSION: patch('app.globus.remove_permission'),
    REMOVE_MEMBER: patch('app.state.ProjectMember.delete_instance'),
    REMOVE_DATASET: patch('app.state.Dataset.delete_instance'),
    UPDATE_DATASET_PROJECT: patch('app.state.Dataset.update_project_id'),
    # functions which query the state of the app
    PREVIOUS_DATASETS: patch('app.state.Dataset.get_previous_datasets', return_value=[]),
    GET_ANALYSES: patch('app.job.get_analyses', return_value=([], [])),
    TRACK_JOB: patch('app.job.track'),
    MEMBER_EXISTS: patch('app.state.ProjectMember.exists', return_value=False),
    PREVIOUS_MEMBERS: patch('app.state.ProjectMember.get_previous_members', return_value=[]),
    DATASET_BY_UUID: patch('app.state.Dataset.where_dataset_uuid', return_value=None),
}

@pytest.fixture
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
    for i in (STAGE, UNSTAGE, INSERT_MEMBER, REMOVE_MEMBER, INSERT_DATASET, REMOVE_DATASET, 
              CREATE_PERMISSION, REMOVE_PERMISSIONS, REMOVE_PERMISSION):
        mock[i].assert_not_called()

def test_new_dataset(mock: dict[int, unittest.mock.MagicMock], dataset):
    app.handle._handle_project(1, [dataset[1]], [])
    mock[INSERT_DATASET].assert_called_once()
    mock[STAGE].assert_called()

def simulate_dataset_state(mock: dict[int, unittest.mock.MagicMock], dataset_uuids, project_id=1):
    '''Set the state of the app with respect to datasets, i.e. simulate
    putting datasets in the database.'''
    def get_dataset(uuid):
        if uuid in dataset_uuids:
            return app.state.Dataset(uuid=uuid, project_id=project_id, dir_path='whatever')        
        else:
            return None
    mock[DATASET_BY_UUID].side_effect = get_dataset

def test_reassigned_dataset(mock: dict[int, unittest.mock.MagicMock], dataset, member):
    simulate_dataset_state(mock, [dataset[1]['uuid']])
    # reassign 'dataset 1' to project 2
    NEW_PROJECT_ID = 2
    app.handle._handle_project(NEW_PROJECT_ID, [dataset[1]], [])
    mock[UPDATE_DATASET_PROJECT].assert_called_once_with(NEW_PROJECT_ID)
    mock[INSERT_DATASET].assert_not_called()
    mock[STAGE].assert_not_called()

def test_seen_dataset(mock: dict[int, unittest.mock.MagicMock]):
    simulate_dataset_state(mock, [dataset[1]['uuid']])