import http.client
import pytest
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from app import App

log_file = 'tests/proxy_request.log'
logging.basicConfig(filename=log_file, level=logging.INFO)

@pytest.fixture(autouse=True)
def app():
    app = App(('localhost', 9093), logging.getLogger(__name__))
    app_thread = threading.Thread(target=app.run)
    app_thread.start()
    yield
    app.stop()
    app_thread.join()
    with open(log_file, 'w') as f:
        pass # clear the log file

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def _minimum_viable_response(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        self._minimum_viable_response()

    def do_PUT(self):
        self._minimum_viable_response()

    def do_DELETE(self):
        self._minimum_viable_response()

class StoppableHTTPServer(HTTPServer):

    def run(self):
        self.serve_forever()

    def stop(self):
        self.shutdown()

@pytest.fixture(autouse=True)
def sl_server():
    server = StoppableHTTPServer(('localhost', 9091), SimpleHTTPRequestHandler)
    server_thread = threading.Thread(target=server.run)
    server_thread.start()
    yield
    server.stop()
    server_thread.join()

def do_request(port=9092, method="POST", path="/smrt-link/projects"):
    try:
        conn = http.client.HTTPConnection("localhost", port)
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

def test_proxy_running():
    proxy_home_port = 8088
    assert do_request(port=proxy_home_port, method="GET")

def test_app_fixture():
    assert do_request(port=9093, method="GET")
    with open("tests/request.log", "r") as f:
        assert len(f.readlines()) == 1

def test_sl_server_fixture():
    assert do_request(port=9091, method="POST")

def test():
    assert do_request(method="PUT")
    assert do_request(method="POST")
    assert do_request(method="DELETE")
    with open("tests/request.log", "r") as f:
        assert len(f.readlines()) == 3