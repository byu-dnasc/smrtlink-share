import pytest
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from app import App

log_file = 'tests/request.log'
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