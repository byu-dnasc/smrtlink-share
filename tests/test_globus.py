import pytest
import unittest.mock

import app.globus
import app.state
import app

IDENTITY_ID = "19ff6717-c44d-4ab4-983c-1eb2095beba4" # aknaupp@byu.edu

class Dataset(app.BaseDataset):
    def __init__(self, uuid, dir_path):
        self._uuid = uuid
        self._dir_path = dir_path
    @property
    def uuid(self):
        return self._uuid
    @property
    def dir_path(self):
        return self._dir_path

assert app.globus.TRANSFER_CLIENT is not None

def test_invalid_path():
    with unittest.mock.patch('app.logger.error') as log_error:
        dataset = Dataset('uuid', 'invalid')
        member_id = IDENTITY_ID
        app.globus.create_permission(dataset, member_id)
        assert log_error.called

def test_permission_exists():
    with unittest.mock.patch('app.logger.error') as log_error:
        dataset = Dataset('uuid', '/test')
        member_id = IDENTITY_ID
        app.globus.create_permission(dataset, member_id)
        assert log_error.called

def test_success():
    with unittest.mock.patch('app.logger.error') as log_error:
        dataset = Dataset('uuid', '/test')
        member_id = '65af3497-1ad5-4a79-8c5b-cec928605c1c' # adkna@globusid.org
        app.globus.create_permission(dataset, member_id)
        assert not log_error.called