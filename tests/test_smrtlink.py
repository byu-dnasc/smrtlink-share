import app.project as project
import app.smrtlink as smrtlink

def test_sl_client_connect():
    '''Test should fail if SMRT Link is not running on localhost:8243 or if credentials are wrong'''
    try:
        smrtlink.DnascSmrtLinkClient.connect()
    except SystemExit:
        assert False, 'Could not connect to SMRT Link'
    assert True
    
def test_get_project():
    assert project.get(1)
    assert not project.get(9999)

def test_load_db():
    project.load_db()
    assert project.Project.select().count() > 0

def test_get_dataset():
    uuid = '48a71a3e-c97c-43ea-ba41-8c2b31dd32b2'
    assert smrtlink.get_client().get_dataset(uuid).uuid == uuid
    assert not smrtlink.get_client().get_dataset('00000000-0000-0000-0000-000000000001')