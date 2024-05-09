import app.smrtlink as smrtlink
import app.staging as staging
from app.project import NewProject
from app import logger, OutOfSyncError

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

def new_project():
    try:
        project = smrtlink.get_new_project()
        if project is None:
            raise Exception('SMRT Link has no projects (other than the "General Project").')
    except Exception as e:
        logger.error(f'Cannot handle new project request: {e}.')
        return
    if _stage_new_project(project):
        project.save() # only update database if staging was successful

def _get_project(project_id):
    '''Return project if found, else None and log error.'''
    try:
        return smrtlink.get_project(project_id)
    except OutOfSyncError as e:
        logger.info('App is Out-of-Sync with SMRT Link.')
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
    elif type(project) is NewProject:
        if _stage_new_project(project):
            project.save()
    else: # type(project) is UpdatedProject
        try:
            staging.update(project)
            project.save()
        except Exception as e:
            logger.error(f'Cannot stage project: {e}.')

def delete_project(project_id):
    ... # delete project from database
    ... # delete project files
    ... # delete project permissions in Globus
 