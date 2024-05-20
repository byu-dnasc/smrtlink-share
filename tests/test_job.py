import pytest
from unittest.mock import MagicMock, patch
from app.job import _poll
import app.job as job

@patch('app.smrtlink.get_job')
def test_poll_successful_analysis(mock_get_job):
    analysis = MagicMock()
    analysis.id = "123"
    mock_get_job.return_value = {"state": "SUCCESSFUL"}
    staging_function = MagicMock()

    _poll(analysis, staging_function)
    staging_function.assert_called_once_with(analysis)

@patch('time.sleep')
@patch('app.smrtlink.get_job')
def test_poll_eventual_success(mock_get_job, mock_sleep):
    analysis = MagicMock()
    analysis.id = "123"
    mock_get_job.side_effect = [{"state": "RUNNING"}, {"state": "SUCCESSFUL"}]
    staging_function = MagicMock()

    _poll(analysis, staging_function)
    staging_function.assert_called_once_with(analysis)
    mock_sleep.assert_called_once()

@patch('app.smrtlink.get_job')
def test_poll_failed_analysis(mock_get_job):
    analysis = MagicMock()
    analysis.id = "123"
    mock_get_job.return_value = {"state": "FAILED"}
    staging_function = MagicMock()

    _poll(analysis, staging_function)
    staging_function.assert_not_called()

@patch('app.job.logger')
@patch('app.smrtlink.get_job')
def test_poll_timeout(mock_get_job, mock_logger):
    analysis = MagicMock()
    analysis.id = "123"
    mock_get_job.return_value = {"state": "RUNNING"}
    staging_function = MagicMock()

    with patch('app.job.MAX_POLLING_TIME', 0):
        _poll(analysis, staging_function)

    staging_function.assert_not_called()
    mock_logger.error.assert_called_once()

@patch('app.job._get_new_jobs')
@patch('app.job._get_dataset_dirs')
@patch('app.job.smrtlink.get_job_files')
@patch('app.job.smrtlink.get_job_datasets')
def test_get_analyses(get_job_datasets, get_job_files, get_dataset_dirs, get_new_jobs):
    get_new_jobs.return_value = [{'name': 'analyze', "id": "123", "state": "SUCCESSFUL"}]
    get_job_datasets.return_value = [1]
    get_dataset_dirs.return_value = ["dir1"]
    get_job_files.return_value = ["file1"]
    completed, pending = job.get_analyses()

    assert len(completed) == 1
    assert len(pending) == 0