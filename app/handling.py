import app.smrtlink as smrtlink
import app.staging as staging
from app.project import NewProject, UpdatedProject
from app import logger, OutOfSyncError
import app.job as job

def _stage_new_project(project):
    '''
    Stage a new project. Return True if successful, False otherwise.
    Log an error if staging raises an exception.
    '''
    try:
        staging.new(project)
    except Exception as e:
        logger.error(f'Cannot stage project: {e}.')
        return False
    return True

def _stage(project):
    if type(project) is NewProject:
        return _stage_new_project(project)
    elif type(project) is UpdatedProject:
        return _stage_project_update(project)
    else:
        logger.error(f'Cannot stage project: {project} is not a recognized project type.')
        return False

def _get_new_project():
    try:
        project = smrtlink.get_new_project()
        if project is None:
            raise Exception('SMRT Link has no projects (other than the "General Project").')
        return project
    except OutOfSyncError as e:
        logger.info('App is Out-of-Sync with SMRT Link: received a request to create a new project, but the most recent project is not new to the app.')
        return e.project
    except Exception as e:
        logger.error(f'Cannot handle new project request: {e}.')
    return None

def new_project():
    project = _get_new_project()
    if project is None:
        return
    if _stage(project):
        project.save() # only update database if staging was successful
    analyses = job.get_analyses(project.datasets, project.id)

def _get_project(project_id):
    '''Return project if found, else None and log error.'''
    try:
        return smrtlink.get_project(project_id)
    except OutOfSyncError as e:
        logger.info('App is Out-of-Sync with SMRT Link: received a request to update a project that the app had not previously staged.')
        return e.project
    except Exception as e:
        logger.error(f'Cannot handle project update request: {e}.')
        return None

def update_project(project_id):
    '''Stage project by updating previously staged project files, unless
    the turns out to be new to the app, in which case stage the project
    using another method.
    '''
    project = _get_project(project_id)
    if project is None:
        return
    if _stage(project):
        project.save()
    
def delete_project(project_id):
    ... # delete project from database
    ... # delete project files
    ... # delete project permissions in Globus
 
def new_job(created_after):
    job_d = job.get_new()
    projects, datasets, job_d = job.get(job_id)