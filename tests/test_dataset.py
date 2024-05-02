import os
import app.dataset as dataset
from app.dataset import Dataset, Parent, Child

username = os.environ.get('USER')
TOMATO_PARENT = 'tests/tomatoes/pb_formats/m84100_240301_194028_s1.hifi_reads.consensusreadset.xml'
TOMATO_20 = 'tests/tomatoes/pb_formats/m84100_240301_194028_s1.hifi_reads.bc1047.consensusreadset.xml'
TOMATO_21 = 'tests/tomatoes/pb_formats/m84100_240301_194028_s1.hifi_reads.bc1048.consensusreadset.xml'

def test_pbcore_dataset():
    ds = dataset.DatasetXml(TOMATO_PARENT)
    sample_datasets = []
    for xml in [res.resourceId for res in ds.externalResources if res.resourceId.endswith('.xml')]: # FIXME: implement function to get XMLs from external resources
        assert os.path.exists(xml)
        sample_datasets.append(dataset.DataSet(xml))
    assert True

def test_tomato_parent():
    ds = Dataset(**{
        'name': 'dataset1',
        'uuid': '1',
        'path': TOMATO_PARENT,
        'numChildren': 2,
    })
    assert type(ds) is Parent
    assert {c_ds.xml_path for c_ds in ds.child_datasets} == {TOMATO_20, TOMATO_21}
    assert {c_ds.barcode for c_ds in ds.child_datasets} == {'bc1047--bc1047', 'bc1048--bc1048'}
    assert {c_ds.name for c_ds in ds.child_datasets} == {'Tomato 20', 'Tomato 21'}
    assert all(c_ds.parent is ds for c_ds in ds.child_datasets)
    assert ds.movie_id == 'm84100_240301_194028_s1'
    assert all(c_ds.movie_id == 'm84100_240301_194028_s1' for c_ds in ds.child_datasets)
    assert len(ds.files) == 19

def test_tomato_20():
    ds = Dataset(**{
        'name': 'dataset1',
        'uuid': '1',
        'path': TOMATO_20,
        'numChildren': 0,
    })
    assert type(ds) is Child
    assert ds.barcode == 'bc1047--bc1047'
    assert ds.name == 'Tomato 20'
    assert ds.movie_id == 'm84100_240301_194028_s1'
    assert len(ds.files) == 2