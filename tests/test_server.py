'''
These tests are for the App class found in the server.py file.
The objective here is to check that the server receives requests,
responds to them, and logs them.
'''
from requests import request
import pytest
import logging
import threading

from app.project import Project
from app.server import App, new_project
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

def do_request(method, path):
    try:
        response = request(method, f"http://localhost:{APP_PORT}{path}")
        return response.status_code
    except Exception as e:
        raise Exception(f'Request "{method} {path}" failed: {e}')

def test_RequestHandler():
    # get the server running
    try:
        app = App(('localhost', APP_PORT))
    except OSError as e:
        raise Exception(f"Port {APP_PORT} was probably already in use.")
    app_thread = threading.Thread(target=app.run)
    app_thread.start()

    # send some invalid requests
    assert do_request("POST", "/smrt-link/projects/1") == 404
    assert do_request("PUT", "/smrt-link/projects") == 404
    assert do_request("DELETE", "/smrt-link/projects") == 404

    # send some valid requests
    assert do_request("GET", "/") == 200
    assert do_request("POST", "/smrt-link/projects") == 200
    assert do_request("PUT", "/smrt-link/projects/1") == 405
    assert do_request("DELETE", "/smrt-link/projects/1") == 405
    assert do_request("PUT", "/smrt-link/projects/2") == 200
    assert do_request("DELETE", "/smrt-link/projects/2") == 200

    # stop the server
    app.stop()
    app_thread.join()
    app_log.clear()

def test_new_project():
    project = Project()
    from app.smrtlink import get_new_project
    get_new_project = lambda x: project
