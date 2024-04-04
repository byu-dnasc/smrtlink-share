from requests import HTTPError
from project import Project
from smrtlink_client import SmrtLinkClient
from dataset import DnascDataSet

class OutOfSyncError(Exception):
    pass

def _dict_to_project(dct):
    '''
    Adapt data obtained from SMRT Link to populate a Project object.
    '''
    members = [member['login'] for member in dct['members']]
    dct['members'] = ', '.join(members[1:]) # ignore the first member (project owner)
    dct['dataset_ids'] = [dataset['uuid'] for dataset in dct['datasets']]
    return Project(**dct)

class DnascSmrtLinkClient(SmrtLinkClient):

    def _get_project_dict(self, id):
        '''
        Returns a dictionary of project data, or None if not found.
        Dictionary includes lists of project datasets and members.
        '''
        try:
            return self.get(f"/smrt-link/projects/{id}")
        except HTTPError as e:
            assert e.response.status_code == 404, 'Unexpected error when getting project from SMRT Link'
            return None
    
    def _get_project_ids(self):
        '''Returns the ids of all projects in SMRT Link.'''
        lst = self.get("/smrt-link/projects")
        return [dct['id'] for dct in lst]
    
    def get_project(self, id):
        '''Get a project from SMRT Link by id.'''
        project_dict = self._get_project_dict(id)
        if project_dict:
            return _dict_to_project(project_dict)
        return None

    def get_new_project(self):
        db_ids = Project.select(Project.id)
        sl_ids = self._get_project_ids()

        offset = len(sl_ids) - len(db_ids)
        if offset == 0:
            return None
        elif offset > 1:
            raise OutOfSyncError()

        return self.get_project(sl_ids[-1])
    
    def get_dataset(self, uuid):
        '''
        param uuid: The UUID of a dataset of any type
        return: a DataSet object, or None if not found
        '''
        ds = self.get_dataset_search(uuid) # 404 safe
        if ds is None:
            return None
        num_children = 0
        if hasattr(ds, 'numChildren'):
            num_children = ds['numChildren']
        return DnascDataSet(ds['uuid'], ds['path'], ds['name'], num_children)
    
    @staticmethod
    def connect():
        '''Returns SmrtLinkClient, or exits if cannot connect'''
        try:
            return DnascSmrtLinkClient(
                host="localhost",
                port=8243,
                username="admin",
                password="admin",
                verify=False # Disable SSL verification (optional, default is True, i.e. SSL verification is enabled)
            )
        except Exception as e:
            print(e)
            exit(1)

    @staticmethod 
    def get_instance(): 
        if not hasattr(DnascSmrtLinkClient, "_instance"): 
            DnascSmrtLinkClient._instance = DnascSmrtLinkClient.connect() 
        return DnascSmrtLinkClient._instance

def get_client():
    return DnascSmrtLinkClient.get_instance()

def load_db():
    sl_client = get_client()
    projects = []
    for id in sl_client.get_project_ids():
        project_dict = sl_client.get_project_dict(id)
        projects.append(_dict_to_project(project_dict))
    Project.bulk_create(projects)