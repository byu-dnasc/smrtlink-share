import http.client
import pytest
import logging
import threading
import os

from app import App

log_file = f'{os.path.dirname(__file__)}/app_request.log'
logging.basicConfig(filename=log_file, level=logging.INFO, force=True)

@pytest.fixture(autouse=True)
def app():
    app = App(('localhost', 9091), logging.getLogger(__name__))
    app_thread = threading.Thread(target=app.run)
    app_thread.start()
    yield
    app.stop()
    app_thread.join()
    with open(log_file, 'w') as f:
        pass # clear the log file

def do_request(method="POST", path="/smrt-link/projects"):
    try:
        conn = http.client.HTTPConnection("localhost", 9091)
        try:
            conn.request(method, path)
            response = conn.getresponse() # prevent ConnectionAbortedError on the server side
            if response.status == 200:
                return True
            return False
        except ConnectionRefusedError:
            print("Connection refused, i.e. no server listening on that port.")
            return False
    finally:
        conn.close()

def test_app_fixture():
    assert do_request(method="GET")
    with open(log_file, "r") as f:
        assert len(f.readlines()) == 1

def test():
    assert do_request(method="PUT")
    assert do_request(method="POST")
    assert do_request(method="DELETE")
    with open(log_file, "r") as f:
        assert len(f.readlines()) == 3