import os

import app.collection
import test.data
import app.xml

username = os.environ.get('USER')

def test_dataset():
    '''Test the case of a dataset with no children'''
    ds = app.collection.Dataset(**{
        'name': 'dataset1',
        'uuid': '1',
        'path': test.data.TOMATO_21,
        'numChildren': 0,
    })
    assert type(ds) is app.collection.Dataset
    assert ds.name == 'dataset1'
    assert ds.movie_id == 'm84100_240301_194028_s1'
    assert len(ds.files) == 2

def test_orphaned_child():
    '''Test the case of a child dataset when the parent is not provided.

    The presence of parentUuid signals that the dataset is a child, but
    since this child has not parent, the only special treatment it gets
    is to use the BioSample name "Tomato 21".
    '''
    ds = app.collection.Dataset(**{
        'name': 'dataset1',
        'uuid': '1',
        'path': test.data.TOMATO_21,
        'numChildren': 0,
        'parentUuid': 'parent_uuid'
    })
    assert type(ds) is app.collection.Dataset
    assert ds.name == 'Tomato 21'
    assert ds.movie_id == 'm84100_240301_194028_s1'
    assert len(ds.files) == 2

def test_tomato_parent():
    '''Test the case of a parent dataset'''
    ds = app.collection.Dataset(**{
        'name': 'dataset1',
        'uuid': '1',
        'path': test.data.TOMATO_PARENT,
        'numChildren': 2,
    })
    assert type(ds) is app.collection.Parent
    assert ds.name == 'Germany tomato 20 and 21'
    assert len(ds.child_datasets) == 3 # two children, plus supplemental resources

def test_tomato_20():
    '''Test the case of a child dataset'''
    ds = app.collection.Child('parent_dir', **{
        'name': 'dataset1',
        'uuid': '1',
        'path': test.data.TOMATO_20,
        'numChildren': 0,
    })
    assert ds.barcode == 'bc1047--bc1047'
    assert ds.name == 'Tomato 20'
    assert len(ds.files) == 2

def test_supplemental_resources():
    ds = app.collection.SupplementalResources('parent', ['file1', 'file2'])
    assert ds.dir_path == 'parent/Supplemental Run Data'
    assert ds.files == ['file1', 'file2']
