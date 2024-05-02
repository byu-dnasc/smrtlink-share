import app.smrtlink as smrtlink
import app.staging as staging
from app import logger, OutOfSyncError

def stage_new_project(project):
    '''
    Stage a new project. Return True if successful, False otherwise.
    Log an error if staging fails.
    '''
    try:
        staging.new(project)
    except Exception as e:
        ... # handle staging exception
        ... # log the error
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
    if stage_new_project(project):
        project.save() # only update database if staging was successful

def update_project(project_id):
    try:
        project = smrtlink.get_project(project_id)
    except OutOfSyncError as e:
        logger.info(f'App is Out-of-Sync with SMRT Link: {e}')
        project = e.project
    except Exception as e:
        logger.error(f'Cannot handle project update request: {e}.')
        return
    if project.is_new:
        if not stage_new_project(project):
            return
    else:
        try:
            staging.update(project)
        except Exception as e:
            ... # handle staging exception
            ... # log the error
            return
    project.save() # only update database if staging was successful

def delete_project(project_id):
    ... # delete project from database
    ... # delete project files
    ... # delete project permissions in Globus
 