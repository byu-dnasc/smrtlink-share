import os
import pytest
import project
import peewee as pw
import smrtlink

@pytest.fixture(autouse=True)
def db():
    '''Adapt functionality in project.init_db() for using an in-memory database'''
    db = pw.SqliteDatabase(':memory:')
    project.Project.bind(db)
    db.connect() # open a connection so that the in-memory database stays alive
    db.create_tables([project.Project], safe=True)
    yield
    db.close()

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
    assert smrtlink.get_client().get_dataset(uuid)['uuid'] == uuid
    assert not smrtlink.get_client().get_dataset('00000000-0000-0000-0000-000000000001')

def collect_hifi_files(path):
    file_list = []
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            if not 'fail_reads' in file_path:
                file_list.append(file_path)
    return file_list

def test_dataset_wrapper():
    username = os.environ.get('USER')
    path = f'/home/{username}/smrtlink-container/data/L9j.pacb'
    hifi_files = collect_hifi_files(path)
    xml_path = f'{path}/pb_formats/m84100_240301_194028_s1.hifi_reads.consensusreadset.xml'
    primary_ds = smrtlink.DataSetWrapper(xml_path)
    sub_datasets = [] # not used in this test
    for xml in [f for f in primary_ds.primary_files if f.endswith('.xml')]:
        assert os.path.exists(xml)
        sub_datasets.append(smrtlink.DataSetWrapper(xml))
    assert not sorted(hifi_files) == sorted(primary_ds.primary_files + primary_ds.supplemental_files)