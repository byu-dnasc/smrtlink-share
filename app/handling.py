import app.smrtlink as smrtlink
import app.staging as staging
import app.globus as globus
from app.project import NewProject, Project, UpdatedProject
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

def _stage_analyses(completed, pending):
    '''
    Stage completed analyses, and track pending analyses.
    '''
    for analysis in completed:
        project = Project(id=analysis.project_id)
        staging.analysis(project, analysis)
    for completed_analysis in job.track(pending):
        project = Project(id=completed_analysis.project_id)
        staging.analysis(project, completed_analysis)

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
    project: Project = _get_new_project()
    if project is None:
        return
    if _stage(project):
        project.save() # only update database if staging was successful
    for updated_project in project.effects:
        _stage(updated_project)
        updated_project.save() # remove rows associating stolen datasets with their previous project
    globus.new(project) # TODO: handle exceptions
    try:
        completed, pending = job.get_project_analyses(project.id)
    except Exception as e:
        logger.error(f'Failed to get new analyses: {e}')
        return
    _stage_analyses(completed, pending)

def update_project(project_id):
    '''
    Handle a notification that a given project was updated in SMRT Link.

    In addition to updating the project, this function stages any 
    completed analyses associated with the project which have not already
    been staged. This staging is redundant, but is intended as a backup 
    in case the app did not receive a notification for a new analysis.
    '''
    project = _get_project(project_id)
    if project is None:
        return
    if _stage(project):
        project.save()
    for updated_project in project.effects:
        _stage(updated_project)
        updated_project.save() # remove rows associating stolen datasets with their previous project
    globus.update(project) # TODO: handle exceptions
    for analysis in job.get_new_project_analyses(project.id):
        staging.analysis(project, analysis)
    
def delete_project(project_id):
    ... # delete project from database
    ... # delete project files
    ... # delete project permissions in Globus

def update_analyses():
    try:
        pending_analyses, completed_analyses = job.get_new_analyses()
    except Exception as e:
        logger.error(f'Failed to update analyses: {e}')
        return
    _stage_analyses(completed_analyses, pending_analyses)