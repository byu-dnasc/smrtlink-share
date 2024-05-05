from unittest.mock import patch, MagicMock
from app import OutOfSyncError
from app.handling import new_project, _stage_new_project, update_project, _get_project
from unittest.mock import patch

@patch('app.handling.staging.new')
@patch('app.handling.logger')
def test_stage_new_project_exception(mock_logger, mock_staging_new):
    '''Case where staging raises an exception.
    Result: Error is logged and False is returned.
    '''
    mock_staging_new.side_effect = Exception('Staging failed.')
    assert not _stage_new_project(None)
    mock_logger.error.assert_called_once()

@patch('app.handling.staging.new')
def test_stage_new_project_success(mock_staging_new):
    '''Case where staging succeeds.
    Result: True is returned.
    '''
    assert _stage_new_project(None)

@patch('app.handling.logger')
@patch('app.smrtlink.get_new_project')
def test_new_projects_no_projects_found(mock_get_new_project, mock_logger):
    '''Case where no projects are found in SMRT Link.
    Result: no modification to project files or database, error logged.
    '''
    mock_get_new_project.return_value = None
    new_project()
    mock_logger.error.assert_called_once()
    
@patch('app.handling.smrtlink.get_new_project')
@patch('app.handling._stage_new_project')
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
@patch('app.handling._stage_new_project')
def test_new_project_staging_fails(mock_stage_new_project, mock_get_new_project):
    '''Case where project is available, but staging fails.
    Result: Project files are not updated, nor the database.
    '''
    mock_project = MagicMock()
    mock_get_new_project.return_value = mock_project
    mock_stage_new_project.return_value = False

    new_project()

    mock_get_new_project.assert_called_once()
    mock_stage_new_project.assert_called_once_with(mock_project)
    mock_project.save.assert_not_called()

@patch('app.handling._get_project')
@patch('app.handling._stage_new_project')
def test_update_project_new(mock_stage_new_project, mock_get_project):
    '''Case where app is out of sync with SMRT Link, so the staging.new function is
    used.
    Result: Project files and database are updated, plus a message is logged as "info"
    '''
    mock_project = MagicMock()
    mock_project.is_new = True
    mock_get_project.return_value = mock_project
    mock_stage_new_project.return_value = True
    update_project(1)
    mock_get_project.assert_called_once()
    mock_stage_new_project.assert_called_once_with(mock_project)
    mock_project.save.assert_called()

@patch('app.handling.smrtlink.get_project')
@patch('app.handling.staging.update')
def test_update_project_update(mock_staging_update, mock_get_project):
    '''Case under normal conditions.
    Result: Project files and database are updated.
    '''
    mock_project = MagicMock()
    mock_project.is_new = False
    mock_get_project.return_value = mock_project
    mock_staging_update.return_value = True
    update_project(1)
    mock_get_project.assert_called_once()
    mock_staging_update.assert_called_once_with(mock_project)
    mock_project.save.assert_called_once()

@patch('app.handling.logger')
@patch('app.handling.smrtlink.get_project')
@patch('app.handling.staging.update')
def test_update_project_update_staging_error(mock_staging_update, mock_get_project, mock_logger):
    '''Case where staging.update raises an exception.
    Result: No modifications to project files or database, error is logged.
    '''
    mock_project = MagicMock()
    mock_project.is_new = False
    mock_get_project.return_value = mock_project
    mock_staging_update.side_effect = Exception()
    update_project(1)
    mock_get_project.assert_called_once()
    mock_staging_update.assert_called_once_with(mock_project)
    mock_project.save.assert_not_called()
    mock_logger.error.assert_called_once()

@patch('app.handling.logger')
@patch('app.handling.smrtlink.get_project')
def test_get_project_smrtlink_error(mock_smrtlink_get_project, mock_logger):
    '''Case where getting project from SMRT Link raises an exception,
    but not OutOfSync error.
    Result: Return None and log error.
    '''
    mock_smrtlink_get_project.side_effect = Exception()
    assert _get_project(1) is None
    mock_logger.error.assert_called_once()

@patch('app.handling.logger')
@patch('app.handling.smrtlink.get_project')
def test_get_project_out_of_sync(mock_smrtlink_get_project, mock_logger):
    '''Case where getting project from SMRT Link raises OutOfSyncError.
    Result: Return project and log info.
    '''
    mock_project = MagicMock()
    mock_smrtlink_get_project.side_effect = OutOfSyncError(mock_project)
    assert _get_project(1) is mock_project
    mock_logger.info.assert_called_once()

@patch('app.handling.smrtlink.get_project')
def test_get_project(mock_smrtlink_get_project):
    '''Case where getting project from SMRT Link is successful.
    Result: Return project.
    '''
    mock_project = MagicMock()
    mock_smrtlink_get_project.return_value = mock_project
    assert _get_project(1) is mock_project