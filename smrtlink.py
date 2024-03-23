from requests import HTTPError
from smrtlink_client import SmrtLinkClient
from pbcore.io.dataset.DataSetIO import DataSet
from pbcore.io.dataset.DataSetMembers import ExternalResource

def get_file_path(res, file_paths):
    if hasattr(res, 'resourceId'):
        file_paths.append(res.resourceId)
    if type(res) is ExternalResource: # else is FileIndex
        if len(res.indices) > 0:
            get_file_paths(res.indices, file_paths)
        if len(res.externalResources) > 0:
            get_file_paths(res.externalResources, file_paths)
    return file_paths

def get_file_paths(resources, file_paths):
    for res in resources:
        get_file_path(res, file_paths)
    return file_paths

class DataSetWrapper:
    '''
    XML Schema definitions found at https://github.com/PacificBiosciences/PacBioFileFormats 
    - ExternalResources, SupplementalResources is found in PacBioBaseDataModel.xsd
    - DataSet and derivative types are found in PacBioDatasets.xsd
    '''
    def __init__(self, xml_path):
        ds = DataSet(xml_path)
        self.primary_files = get_file_paths(ds.externalResources, [])
        self.supplemental_files = get_file_paths(ds.supplementalResources, [])

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
        '''Returns a dictionary of dataset data, or None if not found.'''
        try:
            return self.get_consensusreadset(uuid)
        except HTTPError as e:
            assert e.response.status_code == 404, 'Unexpected error when getting dataset from SMRT Link'
            return None
    
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