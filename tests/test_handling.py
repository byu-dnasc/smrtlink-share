from unittest.mock import patch, MagicMock
from app.handling import new_project
from unittest.mock import patch

@patch('app.handling.logger')
@patch('app.smrtlink.get_new_project')
def test_logging(mock_get_new_project, mock_logger):
    mock_get_new_project.return_value = None
    new_project()
    mock_logger.error.assert_called_once()
    
@patch('app.handling.smrtlink.get_new_project')
@patch('app.handling.stage_new_project')
@patch('app.handling.Project')
def test_new_project(mock_Project, mock_stage_new_project, mock_get_new_project):
    # Mock the return value of smrtlink.get_new_project
    mock_project = MagicMock()
    mock_get_new_project.return_value = mock_project

    # Mock the return value of stage_new_project
    mock_stage_new_project.return_value = True

    # Mock the Project class
    mock_project_class = MagicMock()
    mock_Project.return_value = mock_project_class

    # Call the function
    new_project()

    # Assert that smrtlink.get_new_project was called
    mock_get_new_project.assert_called_once()

    # Assert that stage_new_project was called with the mock project
    mock_stage_new_project.assert_called_once_with(mock_project)

    # Assert that the project was saved
    mock_project_class.save.assert_called_once()
