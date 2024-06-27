import unittest.mock
import pytest

import test.data
import app.handle

ERROR = 0
STAGE = 1
UNSTAGE = 2
TRACK_JOB = 3
ADD_MEMBER = 4
MEMBER_EXISTS = 5
PREVIOUS_MEMBERS = 6
DATASET_BY_ID = 7
ADD_DATASET = 8
PREVIOUS_DATASETS = 9
CREATE_PERMISSION = 10
REMOVE_PERMISSIONS = 11
REMOVE_PERMISSION = 12
GET_ANALYSES = 13

from unittest.mock import patch
patchers = {
    ERROR: patch('app.logger.error'),
    STAGE: patch('app.filesystem.stage', return_value=True),
    UNSTAGE: patch('app.filesystem.remove', return_value=True),
    TRACK_JOB: patch('app.job.track'),
    ADD_MEMBER: patch('app.state.ProjectMember.add'),
    MEMBER_EXISTS: patch('app.state.ProjectMember.exists', return_value=False),
    PREVIOUS_MEMBERS: patch('app.state.ProjectMember.get_previous_members', return_value=[]),
    DATASET_BY_ID: patch('app.state.Dataset.where_dataset_id', return_value=None),
    ADD_DATASET: patch('app.state.Dataset.add'),
    PREVIOUS_DATASETS: patch('app.state.Dataset.get_previous_datasets', return_value=[]),
    CREATE_PERMISSION: patch('app.globus.create_permission'),
    REMOVE_PERMISSIONS: patch('app.globus.remove_permissions'),
    REMOVE_PERMISSION: patch('app.globus.remove_permission'),
    GET_ANALYSES: patch('app.job.get_analyses', return_value=([], []))
}

@pytest.fixture()
def mock():
    mocks = {i: patcher.start() for i, patcher in patchers.items()}
    yield mocks
    unittest.mock.patch.stopall()

def test_empty_project(mock: dict[int, unittest.mock.MagicMock]):
    app.handle._handle_project(test.data.PROJECT_1)
    mock[ADD_MEMBER].assert_called_once()
    mock[ADD_DATASET].assert_called_once()
    mock[CREATE_PERMISSION].assert_called_once()
    mock[STAGE].assert_called_once()

def test_new_dataset(mock: dict[int, unittest.mock.MagicMock]):
    project = test.data.PROJECT_1
    project['datasets'].append(test.data.DATASET_1)
    app.handle._handle_project(test.data.PROJECT_1)
    mock[ADD_DATASET].assert_called_once()
    mock[STAGE].assert_called_once()