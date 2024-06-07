import os
import app.xml
import app.collection as collection
from app.collection import Dataset, Parent, Child

username = os.environ.get('USER')
TOMATO_PARENT = 'tests/tomatoes/pb_formats/m84100_240301_194028_s1.hifi_reads.consensusreadset.xml'
TOMATO_20 = 'tests/tomatoes/pb_formats/m84100_240301_194028_s1.hifi_reads.bc1047.consensusreadset.xml'
TOMATO_21 = 'tests/tomatoes/pb_formats/m84100_240301_194028_s1.hifi_reads.bc1048.consensusreadset.xml'

def test_pbcore_dataset():
    ds = app.xml.DatasetXml(TOMATO_PARENT)
    sample_datasets = []
    for xml in [res.resourceId for res in ds.externalResources if res.resourceId.endswith('.xml')]: # FIXME: implement function to get XMLs from external resources
        assert os.path.exists(xml)
        sample_datasets.append(collection.DataSet(xml))
    assert True

def test_dataset():
    '''Test the case of a dataset with no children'''
    ds = Dataset(**{
        'name': 'dataset1',
        'uuid': '1',
        'path': TOMATO_21,
        'numChildren': 0,
    })
    assert type(ds) is Dataset
    assert ds.name == 'dataset1'
    assert ds.movie_id == 'm84100_240301_194028_s1'
    assert len(ds.files) == 2

def test_orphaned_child():
    '''Test the case of a child dataset when the parent is not provided.

    The presence of parentUuid signals that the dataset is a child, but
    since this child has not parent, the only special treatment it gets
    is to use the BioSample name "Tomato 21".
    '''
    ds = Dataset(**{
        'name': 'dataset1',
        'uuid': '1',
        'path': TOMATO_21,
        'numChildren': 0,
        'parentUuid': 'parent_uuid'
    })
    assert type(ds) is Dataset
    assert ds.name == 'Tomato 21'
    assert ds.movie_id == 'm84100_240301_194028_s1'
    assert len(ds.files) == 2

def test_tomato_parent():
    '''Test the case of a parent dataset'''
    ds = Dataset(**{
        'name': 'dataset1',
        'uuid': '1',
        'path': TOMATO_PARENT,
        'numChildren': 2,
    })
    assert type(ds) is Parent
    assert ds.name == 'Germany tomato 20 and 21'
    assert len(ds.child_datasets) == 3 # two children, plus supplemental resources

def test_tomato_20():
    '''Test the case of a child dataset'''
    ds = Child('parent_dir', **{
        'name': 'dataset1',
        'uuid': '1',
        'path': TOMATO_20,
        'numChildren': 0,
    })
    assert ds.barcode == 'bc1047--bc1047'
    assert ds.name == 'Tomato 20'
    assert len(ds.files) == 2

def test_supplemental_resources():
    ds = collection.SupplementalResources('parent', ['file1', 'file2'])
    assert ds.dir_path == 'parent/Supplemental Run Data'
    assert ds.files == ['file1', 'file2']

def test_analysis():
    ds = collection.Analysis('parent', 'name', 1, ['file'])
    assert ds.prefix    
    assert ds.dir_name
    assert ds.files