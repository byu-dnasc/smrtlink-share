from unittest.mock import patch, MagicMock
from app import OutOfSyncError
from app.handling import new_project, stage_new_project, update_project
from unittest.mock import patch

@patch('app.handling.staging.new')
@patch('app.handling.logger')
def test_stage_new_project_exception(mock_logger, mock_staging_new):
    '''Case where staging raises an exception.
    Result: Error is logged and False is returned.
    '''
    mock_staging_new.side_effect = Exception('Staging failed.')
    assert not stage_new_project(None)
    mock_logger.error.assert_called_once()

@patch('app.handling.staging.new')
def test_stage_new_project_success(mock_staging_new):
    '''Case where staging succeeds.
    Result: True is returned.
    '''
    assert stage_new_project(None)

@patch('app.handling.logger')
@patch('app.smrtlink.get_new_project')
def test_new_projects_no_projects_found(mock_get_new_project, mock_logger):
    '''Case where no projects are found in SMRT Link.
    Result: no staging, no modification to database, error logged.
    '''
    mock_get_new_project.return_value = None
    new_project()
    mock_logger.error.assert_called_once()
    
@patch('app.handling.smrtlink.get_new_project')
@patch('app.handling.stage_new_project')
def test_new_project_success(mock_stage_new_project, mock_get_new_project):
    '''Case where project is available and staging succeeds.
    Result: Project files are staged and database is updated.
    '''
    mock_project = MagicMock()
    mock_get_new_project.return_value = mock_project
    mock_stage_new_project.return_value = True

    new_project()

    mock_get_new_project.assert_called_once()
    mock_stage_new_project.assert_called_once_with(mock_project)
    mock_project.save.assert_called_once()

@patch('app.handling.smrtlink.get_new_project')
@patch('app.handling.stage_new_project')
def test_new_project_staging_fails(mock_stage_new_project, mock_get_new_project):
    '''Case where project is available, but staging fails.
    Result: Project files are not staged and database is not updated.
    '''
    mock_project = MagicMock()
    mock_get_new_project.return_value = mock_project
    mock_stage_new_project.return_value = False

    new_project()

    mock_get_new_project.assert_called_once()
    mock_stage_new_project.assert_called_once_with(mock_project)
    mock_project.save.assert_not_called()

@patch('app.handling.smrtlink.get_project')
@patch('app.handling.stage_new_project')
def test_update_project_out_of_sync_success(mock_stage_new_project, mock_get_project):
    '''Case where app is out of sync with SMRT Link, but proceeds 
    to stage the project anyway.
    Result: Project files are staged and database is updated.
    '''
    mock_project = MagicMock()
    mock_project.is_new = True
    mock_get_project.side_effect = OutOfSyncError(mock_project)
    mock_stage_new_project.return_value = True
    update_project(1)
    mock_get_project.assert_called_once()
    mock_stage_new_project.assert_called_once_with(mock_project)
    mock_project.save.assert_called()

@patch('app.handling.smrtlink.get_project')
@patch('app.handling.staging.update')
def test_update_project_no_exception(mock_staging_update, mock_get_project):
    '''Case under normal conditions.
    Result: Project files are updated and the new data is saved 
    in the database.
    '''
    mock_project = MagicMock()
    mock_project.is_new = False
    mock_get_project.return_value = mock_project
    mock_staging_update.return_value = True
    update_project(1)
    mock_get_project.assert_called_once()
    mock_staging_update.assert_called_once_with(mock_project)
    mock_project.save.assert_called_once()