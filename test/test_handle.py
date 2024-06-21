import unittest.mock

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

d = {
    ERROR: 'app.logger.error',
    STAGE: 'app.filesystem.stage',
    UNSTAGE: 'app.filesystem.remove',
    TRACK_JOB: 'app.job.track',
    ADD_MEMBER: 'app.state.ProjectMember.add',
    MEMBER_EXISTS: 'app.state.ProjectMember.exists',
    PREVIOUS_MEMBERS: 'app.state.ProjectMember.get_previous_members',
    DATASET_BY_ID: 'app.state.Dataset.where_dataset_id',
    ADD_DATASET: 'app.state.Dataset.add',
    PREVIOUS_DATASETS: 'app.state.Dataset.get_previous_datasets',
    CREATE_PERMISSION: 'app.globus.create_permission',
    REMOVE_PERMISSIONS: 'app.globus.remove_permissions',
    REMOVE_PERMISSION: 'app.globus.remove_permission',
    GET_ANALYSES: 'app.job.get_analyses'
}

@unittest.mock.patch(d[GET_ANALYSES])
@unittest.mock.patch(d[REMOVE_PERMISSION])
@unittest.mock.patch(d[REMOVE_PERMISSIONS])
@unittest.mock.patch(d[CREATE_PERMISSION])
@unittest.mock.patch(d[PREVIOUS_DATASETS])
@unittest.mock.patch(d[ADD_DATASET])
@unittest.mock.patch(d[DATASET_BY_ID])
@unittest.mock.patch(d[PREVIOUS_MEMBERS])
@unittest.mock.patch(d[MEMBER_EXISTS])
@unittest.mock.patch(d[ADD_MEMBER])
@unittest.mock.patch(d[TRACK_JOB])
@unittest.mock.patch(d[UNSTAGE])
@unittest.mock.patch(d[STAGE])
@unittest.mock.patch(d[ERROR])
class Test:
    def test_sanity(self, *mock):
        '''Make sure that the constant values correspond to 
        the correct mock object.'''
        for i, m in enumerate(mock):
            assert m._mock_name == d[i].split('.')[-1]

    def test_logger(self, *mock):
        app.logger.error('ahhhhhhhhh')
        assert mock[ERROR].called
    
    def test_proj1(self, *mock):
        app.handle.new_project(test.data.PROJECT_1)