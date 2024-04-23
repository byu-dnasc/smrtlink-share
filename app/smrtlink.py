from requests import HTTPError
from app.project import Project
from app.smrtlink_client import SmrtLinkClient
from app import get_env_var, OutOfSyncError

class DnascDataSet:
    def __init__(self, uuid, name, path, num_children):
        self.uuid = uuid
        self.name = name
        self.path = path
        self.num_children = num_children

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

HOST = get_env_var('SMRTLINK_HOST')
PORT = get_env_var('SMRTLINK_PORT')
USER = get_env_var('SMRTLINK_USER')
PASS = get_env_var('SMRTLINK_PASS')

def _get_smrtlink_client():
    """
    Gets DnascSmrtLinkClient object
    """
    try:
        return DnascSmrtLinkClient(
            host=HOST,
            port=PORT,
            username=USER,
            password=PASS,
            verify=False # Disable SSL verification (optional, default is True, i.e. SSL verification is enabled)
        )
    except Exception as e:
        return None

CLIENT = _get_smrtlink_client()
    
def get_project(id):
    '''Get a project from SMRT Link by id by calling get_project_dict method.'''
    project_dict = CLIENT.get_project_dict(id)
    if project_dict:
        return Project(**project_dict)
    return None

def get_new_project():
    """Gets all of the projects and project IDs. Checks to see if there are more 
    sl projects than db projects. If the difference is greater than one, it will 
    raise an error. Otherwise it will return the newest project.
    """
    db_ids = Project.select(Project.id)
    sl_ids = CLIENT.get_project_ids()

    offset = len(sl_ids) - len(db_ids)
    if offset == 0:
        return None
    elif offset > 1:
        raise OutOfSyncError()

    return get_project(sl_ids[-1])

def load_db():
    projects = []
    for id in CLIENT.get_project_ids():
        project_dict = CLIENT.get_project_dict(id)
        projects.append(Project(**project_dict))
    Project.bulk_create(projects)