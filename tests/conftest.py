import pytest
import json
import smrtlink

def get_project_dicts():
    with open('tests/projects.json') as f:
        return json.load(f)

def get_dataset_dict():
    with open('tests/datasets.json') as f:
        return json.load(f)

@pytest.fixture()
def sl():
    '''
    Hack to replace the SmrtLinkClient instance with the "test client".
    '''
    class SmrtLinkTestClient:
        '''Mimic DnascSmrtLinkClient for more convenience in testing.'''
        project_dicts = get_project_dicts()
        dataset_dict = get_dataset_dict()
        def get_project_dict(self, id):
            zero_based_id = id - 1
            if zero_based_id < 0 or zero_based_id >= len(self.project_dicts):
                return None
            return self.project_dicts[zero_based_id]
        def get_project_ids(self):
            return [p_d['id'] for p_d in self.project_dicts]
        def get_dataset(self, uuid):
            if uuid in self.dataset_dict.keys():
                return self.dataset_dict[uuid]
            return None
    smrtlink.DnascSmrtLinkClient._instance = SmrtLinkTestClient()

