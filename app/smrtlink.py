import app.smrtlink_client
import app

class DnascSmrtLinkClient(app.smrtlink_client.SmrtLinkClient):

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
            host=app.SMRTLINK_HOST,
            port=app.SMRTLINK_PORT,
            username=app.SMRTLINK_USER,
            password=app.SMRTLINK_PASS,
            verify=False # Disable SSL verification
        )
    except Exception as e:
        return None

CLIENT = _get_smrtlink_client()

def get_jobs_created_after(time):
    '''
    Get jobs from SMRT Link created after `time` and belonging
    to a project other than project 1.

    `time`: a timestamp in the format 'YYYY-MM-DDTHH:MM:SS.sssZ'.
    '''
    return CLIENT.get_analysis_jobs(createdAt='gt:' + time,
                                    projectId='not:1')

def get_job_datasets(id):
    '''Get datasets for a job by id from SMRT Link.'''
    return CLIENT.get_job_datasets(id)

def get_job(id):
    '''Get a job by id from SMRT Link.'''
    return CLIENT.get_job(id)

def get_dataset_jobs(id):
    '''Get jobs for a dataset by id from SMRT Link.'''
    return CLIENT.get_dataset_jobs(id)

def get_job_files(id):
    '''Get files for a job by id from SMRT Link.'''
    return CLIENT.get_job_datastore(id)

def get_project(id):
    '''Raises Exception'''
    project_d = CLIENT.get_project_dict(id)
    return project_d['datasets'], project_d['members']

def get_new_project():
    '''Raises Exception'''
    sl_ids = CLIENT.get_project_ids()
    project_d = CLIENT.get_project_dict(sl_ids[-1])
    return project_d['id'], project_d['datasets'], project_d['members']