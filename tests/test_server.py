'''
These tests are for the App class found in the server.py file.
The objective here is to check that the server receives requests,
responds to them, and logs them.
'''
from requests import request
import pytest
import logging
import threading
import sys

from app.server import App
import app

app_log = []
class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.setFormatter(app.log_formatter)
    def emit(self, record):
        app_log.append(self.format(record))
app.logger.handlers = [ListHandler()]

APP_PORT = 9093

@pytest.fixture(autouse=True)
def setup():
    try:
        app = App(('localhost', APP_PORT))
    except OSError as e:
        raise Exception(f"Port {APP_PORT} was probably already in use.")
    app_thread = threading.Thread(target=app.run)
    app_thread.start()
    yield
    app.stop()
    app_thread.join()
    app_log.clear()

def valid_request(method, path):
    try:
        response = request(method, f"http://localhost:{APP_PORT}{path}")
        return True if response.status_code == 200 else False
    except Exception as e:
        raise Exception(f'Request "{method} {path}" failed: {str(e)}', file=sys.stderr)

def test():
    assert not valid_request("POST", "/smrt-link/projects/1")
    assert not valid_request("PUT", "/smrt-link/projects")
    assert not valid_request("DELETE", "/smrt-link/projects")
    assert valid_request("GET", "/")
    assert valid_request("POST", "/smrt-link/projects")
    assert valid_request("PUT", "/smrt-link/projects/1")
    assert valid_request("DELETE", "/smrt-link/projects/1")
    assert len(app_log) == 7