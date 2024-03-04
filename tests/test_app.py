import pytest
import http.client

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