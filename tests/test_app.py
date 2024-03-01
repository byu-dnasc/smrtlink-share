import pytest
import http.client

def do_request(port=9092, method="POST", path="/smrt-link/projects"):
    try:
        conn = http.client.HTTPConnection("localhost", port)
        try:
            conn.request(method, path)
            return True
        except ConnectionRefusedError:
            print("Connection refused, i.e. no server listening on that port.")
            return False
    except http.client.HTTPException:
        print("HTTP exception occurred.")
        return False
    finally:
        conn.close()

def test_proxy_running():
    proxy_home_port = 8088
    assert do_request(port=proxy_home_port)

@pytest.mark.usefixtures("app")
def test_app_running():
    assert do_request(method="GET")
    with open("request.log", "r") as f:
        assert len(f.readlines()) == 1

def test():
    assert do_request()
    with open("request.log", "r") as f:
        assert len(f.readlines()) == 1