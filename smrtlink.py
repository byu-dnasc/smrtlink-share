from requests import HTTPError
from smrtlink_client import SmrtLinkClient
from dataset import DnascDataSet

class DnascSmrtLinkClient(SmrtLinkClient):

    def get_project_dict(self, id):
        '''
        Returns a dictionary of project data, or None if not found.
        Dictionary includes lists of project datasets and members.
        '''
        try:
            return self.get(f"/smrt-link/projects/{id}")
        except HTTPError as e:
            assert e.response.status_code == 404, 'Unexpected error when getting project from SMRT Link'
            return None
    
    def get_project_ids(self):
        '''Returns the ids of all projects in SMRT Link.'''
        lst = self.get("/smrt-link/projects")
        return [dct['id'] for dct in lst]
    
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