from unittest.mock import patch
import pytest
import threading
from requests import post, put, delete

import app.server as server
from app import APP_PORT

@pytest.fixture(scope='session')
def setup():
    app = server.App(('localhost', APP_PORT))
    app_thread = threading.Thread(target=app.run)
    app_thread.start()
    yield
    app.stop()
    app_thread.join()

pytestmark = pytest.mark.usefixtures("setup")

@pytest.mark.parametrize("request_, uri, error_code", 
    (
        (post, '/smrt-link/projects/1', 404),
        (put, '/smrt-link/projects', 404),
        (delete, '/smrt-link/projects', 404),
        (put, '/smrt-link/projects/1', 405),
        (delete, '/smrt-link/projects/1', 405)
    )
)
def test_invalid_requests(request_, uri, error_code):
    with patch('time.sleep'), \
         patch('app.server.logger') as logger:
        assert request_(f'http://localhost:{APP_PORT}{uri}').status_code == error_code
        assert logger.info.called

@pytest.mark.parametrize("request_, uri, handler", 
    (
        (post, "/smrt-link/projects", 'app.handling.new_project'),
        (put, "/smrt-link/projects/2", 'app.handling.update_project'),
        (delete, "/smrt-link/projects/2", 'app.handling.delete_project'),
        (post, "/smrt-link/job-manager/jobs/analysis", 'app.handling.update_analyses')
    )
)
def test_valid_requests(request_, uri, handler):
    with patch(handler) as handling_function, \
         patch('time.sleep'), \
         patch('app.server.logger') as logger:
        assert request_(f'http://localhost:{APP_PORT}{uri}').status_code == 200
        assert handling_function.called
        assert logger.info.called