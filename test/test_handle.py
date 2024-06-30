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
GET_REMOVED_MEMBERS = 6
GET_DATASET = 7
INSERT_DATASET = 8
GET_REMOVED_DATASETS = 9
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
    GET_REMOVED_DATASETS: patch('app.state.Dataset.get_removed_datasets', return_value=[]),
    GET_ANALYSES: patch('app.job.get_analyses', return_value=([], [])),
    TRACK_JOB: patch('app.job.track'),
    MEMBER_EXISTS: patch('app.state.ProjectMember.exists', return_value=False),
    GET_REMOVED_MEMBERS: patch('app.state.ProjectMember.get_removed_members', return_value=[]),
    GET_DATASET: patch('app.state.Dataset.get_by_dataset_uuid', return_value=None),
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
    return [None, 'user1@globusid.org', 'user2@globusid.org']

def call_handle_project(project_id, dataset_dicts, member_ids):
    for d in dataset_dicts:
        d['projectId'] = project_id
    app.handle._handle_project(project_id, dataset_dicts, member_ids)

def test_empty_project(mock: dict[int, unittest.mock.MagicMock]):
    call_handle_project(1, [], [])
    for i in (STAGE, UNSTAGE, INSERT_MEMBER, REMOVE_MEMBER, INSERT_DATASET, REMOVE_DATASET, 
              CREATE_PERMISSION, REMOVE_PERMISSIONS, REMOVE_PERMISSION):
        mock[i].assert_not_called()

def test_new_dataset(mock: dict[int, unittest.mock.MagicMock], dataset):
    call_handle_project(1, [dataset[1]], [])
    mock[INSERT_DATASET].assert_called_once()
    mock[STAGE].assert_called()

def simulate_app_state(mock: dict[int, unittest.mock.MagicMock], state_project_id, dataset_dicts, member_ids):
    '''
    Set the state of the app with respect to datasets, i.e. simulate
    putting datasets in the database.
    
    What this actually does is create some mock side effects for the functions
    which query the state of the app.
    '''
    def get_dataset(uuid):
        if uuid in [d['uuid'] for d in dataset_dicts]:
            return app.state.Dataset(uuid=uuid, project_id=state_project_id, dir_path='whatever')        
        else:
            return None
    def project_member_exists(project_id, member_id):
        if member_id in member_ids and \
            state_project_id == project_id:
            return True
        return False
    mock[GET_DATASET].side_effect = get_dataset
    mock[MEMBER_EXISTS].side_effect = project_member_exists

def test_reassigned_dataset(mock: dict[int, unittest.mock.MagicMock], dataset):
    simulate_app_state(mock, 1, [dataset[1]], [])
    NEW_PROJECT_ID = 2
    call_handle_project(NEW_PROJECT_ID, [dataset[1]], [])
    mock[UPDATE_DATASET_PROJECT].assert_called_once_with(NEW_PROJECT_ID)
    mock[INSERT_DATASET].assert_not_called()
    mock[STAGE].assert_not_called()

def test_seen_dataset(mock: dict[int, unittest.mock.MagicMock], dataset):
    simulate_app_state(mock, 1, [dataset[1]], [])
    call_handle_project(1, [dataset[1]], [])
    for i in (STAGE, UNSTAGE, INSERT_MEMBER, REMOVE_MEMBER, INSERT_DATASET, REMOVE_DATASET, 
              CREATE_PERMISSION, REMOVE_PERMISSIONS, REMOVE_PERMISSION):
        mock[i].assert_not_called()

def test_new_member(mock: dict[int, unittest.mock.MagicMock], member):
    # case 1
    simulate_app_state(mock, 1, [], [])
    call_handle_project(1, [], [member[1]])
    mock[INSERT_MEMBER].assert_called_once()
    mock[INSERT_MEMBER].reset_mock()
    # case 2
    simulate_app_state(mock, 1, [], [member[1]])
    call_handle_project(1, [], [member[1]])
    mock[INSERT_MEMBER].assert_not_called()
    mock[INSERT_MEMBER].reset_mock()
    # case 3
    simulate_app_state(mock, 1, [], [member[1]])
    call_handle_project(2, [], [member[1]])
    mock[INSERT_MEMBER].assert_called_once()
    mock[INSERT_MEMBER].reset_mock()