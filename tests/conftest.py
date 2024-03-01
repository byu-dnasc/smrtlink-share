import pytest
import threading

from app import App, RequestHandler

@pytest.fixture(autouse=True)
def app():
    app = App(('localhost', 9093), RequestHandler)
    app_thread = threading.Thread(target=app.run)
    app_thread.start()
    yield
    app.stop()
    app_thread.join()