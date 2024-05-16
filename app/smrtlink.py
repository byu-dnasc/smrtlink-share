from requests import HTTPError
from app.project import Project, NewProject, UpdatedProject
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

def get_dataset_jobs(id):
    '''
    Get jobs for a dataset by id from SMRT Link.
    '''
    return CLIENT.get_dataset_jobs(id)

def get_job_files(id):
    '''
    Get files for a job by id from SMRT Link.
    '''
    return CLIENT.get_job_datastore(id)

def get_project(id):
    '''
    Get a project from SMRT Link by id by calling get_project_dict method.
    '''
    project_dict = CLIENT.get_project_dict(id)
    if project_dict:
        project = Project(**project_dict)
        if type(project) is NewProject:
            raise OutOfSyncError(project)
        return project
    return None

def get_new_project():
    '''
    Get the most recent project from SMRT Link, or None if there are no projects.

    Raises error if there is a problem with the connection to SMRT Link,
    or OutOfSyncError if the most recent project in SMRT Link turns 
    out to not be new to the app.
    '''
    sl_ids = CLIENT.get_project_ids()
    project_d = CLIENT.get_project_dict(sl_ids[-1])
    if project_d:
        project = Project(**project_d)
        if type(project) is UpdatedProject:
            raise OutOfSyncError(project)
        return project
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