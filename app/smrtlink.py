from requests import HTTPError
from app.project import Project
from app.smrtlink_client import SmrtLinkClient
from app import get_env_var, OutOfSyncError

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
    elif offset == 1:
        return get_project(sl_ids[-1])
    else: # abs(offset) > 1
        raise OutOfSyncError()

def sync_projects():
    ...

def load_db():
    '''Load the database with projects from SMRT Link.'''
    # clear the database
    Project.delete.execute()
    # repopulate the database
    projects = []
    for id in CLIENT.get_project_ids():
        project_dict = CLIENT.get_project_dict(id)
        projects.append(Project(**project_dict))
    Project.bulk_create(projects)
    return projects