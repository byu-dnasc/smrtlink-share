import app.smrtlink as smrtlink
import app.staging as staging
from app.project import NewProject, UpdatedProject
from app import logger, OutOfSyncError
import app.job as job

def _stage(project):
    '''
    Stage a NewProject or UpdatedProject. Return True if successful, False otherwise.
    Log an error if staging raises an exception.
    '''
    try:
        if type(project) is NewProject:
            staging.new(project)
        elif type(project) is UpdatedProject:
            staging.update(project)
        else:
            raise Exception(f'Expected a NewProject or UpdatedProject, but received a {type(project)}.')
    except Exception as e:
        logger.error(f'Cannot stage project: {e}.')
        return False
    return True

def _get_new_project():
    '''
    Get the most recent project from SMRT Link. This project is expected to be a NewProject,
    but may be an UpdatedProject if the app is Out-of-Sync with SMRT Link.

    Return project. Return None if there are no projects, or if an error occurs.
    '''
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

def _get_project(project_id):
    '''
    Get a project by id from SMRT Link. The project is expected to be an UpdatedProject,
    but may be a NewProject if the app is Out-of-Sync with SMRT Link.

    Return project if found. Return None if the project is not found, or if an error occurs.
    '''
    try:
        return smrtlink.get_project(project_id)
    except OutOfSyncError as e:
        logger.info('App is Out-of-Sync with SMRT Link: received a request to update a project that the app had not previously staged.')
        return e.project
    except Exception as e:
        logger.error(f'Cannot handle project update request: {e}.')
        return None

def new_project():
    '''
    Handle a notification that a new project was created in SMRT Link.
    '''
    project = _get_new_project()
    if project is None:
        return
    if _stage(project):
        project.save() # only update database if staging was successful

def update_project(project_id):
    '''
    Handle a notification that a given project was updated in SMRT Link.

    `project_id` is the id of the project in SMRT Link.
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