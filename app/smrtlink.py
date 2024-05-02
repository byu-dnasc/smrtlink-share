from requests import HTTPError
from app.project import Project
from app.smrtlink_client import SmrtLinkClient
from app import OutOfSyncError, SMRTLINK_HOST, SMRTLINK_PORT, SMRTLINK_USER, SMRTLINK_PASS

class DnascSmrtLinkClient(SmrtLinkClient):

    def get_project_dict(self, id):
        '''
        Returns a dictionary of project data, or None if not found.
        '''
        try:
            return self.get(f"/smrt-link/projects/{id}")
        except Exception as e:
            if e.response.status_code == 404:
                return None
            raise Exception(f'Error getting data from SMRT Link: {e}')
    
    def get_project_ids(self):
        '''
        Returns the ids of all projects in SMRT Link.
        '''
        lst = self.get("/smrt-link/projects")
        return [dct['id'] for dct in lst]
   
def _get_smrtlink_client():
    """
    Gets DnascSmrtLinkClient object
    """
    try:
        return DnascSmrtLinkClient(
            host=SMRTLINK_HOST,
            port=SMRTLINK_PORT,
            username=SMRTLINK_USER,
            password=SMRTLINK_PASS,
            verify=False # Disable SSL verification (optional, default is True, i.e. SSL verification is enabled)
        )
    except Exception as e:
        return None

CLIENT = _get_smrtlink_client()
    
def get_project(id):
    '''
    Get a project from SMRT Link by id by calling get_project_dict method.
    '''
    project_dict = CLIENT.get_project_dict(id)
    if project_dict:
        project = Project(**project_dict)
        if project.is_new:
            raise OutOfSyncError()
        return project
    return None

def get_new_project():
    '''
    Get the most recent project from SMRT Link.
    Raises error there is a problem with the connection to SMRT Link.
    '''
    sl_ids = CLIENT.get_project_ids()
    project_d = CLIENT.get_project_dict(sl_ids[-1])
    if project_d:
        return Project(**project_d)
    return None

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