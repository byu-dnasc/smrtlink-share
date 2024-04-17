from os import listdir, mkdir, makedirs, link, rename, stat, remove, walk
from os.path import join, basename, dirname, exists, isdir
import app.staging as staging
import shutil
import pytest
import os
import app.smrtlink as smrtlink


@pytest.fixture(autouse=True)
def cleanup():
    shutil.rmtree(staging.root, ignore_errors=True)
    mkdir(staging.root)

def test_new():
    staging.new(2)
    assert isdir(join(staging.root, "2/Tomato", "Germany tomato 20 and 21-Cell1 (all samples)"))

def test_delete_dir():
    path = staging.root + "/test_file_dir"
    os.mkdir(path)
    with open(f"{path}/test_file", "w") as f:
        pass
    staging.delete_dir(path)
    assert not exists(f"{path}/test_file")

class TestDataSet:
    def __init__(self):
        self.name = "dataset1"
        self.id = 1
        self.is_super = False
        self.files = []

class TestProject:
    def __init__ (self):
        self.id = "1"
        self.name = "test_obj"
        self.datasets = {
            1:TestDataSet(),
            }
        
def test_update_rename():
    project = TestProject()
    makedirs(join(staging.root, project.id, project.name))
    project.old_name = project.name
    project.name = "new_name"
    staging.update(project)
    assert exists(join(staging.root, project.id, project.name))

def test_update_add_datasets():
    project = TestProject()
    project.datasets_to_add = [1]
    makedirs(join(staging.root, project.id, project.name))
    staging.update(project)
    assert exists(join(staging.root, project.id, project.name, project.datasets[1].name))

def test_datasets_to_remove():
    project = TestProject()
    project.names_of_datasets_to_remove = ["dataset1"]
    makedirs(join(staging.root, project.id, project.name, project.datasets[1].name))
    staging.update(project)
    assert not exists(join(staging.root, project.id, project.name, project.datasets[1].name))