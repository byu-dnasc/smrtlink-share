from os import listdir, mkdir, makedirs, link, rename, stat, remove, walk
from os.path import join, basename, dirname, exists, isdir
import app.staging as staging
from app.staging import DatasetDirectory
import shutil
import pytest
import os
import app.smrtlink as smrtlink
from app.project import Project
from app import STAGING_ROOT

from tests.test_project import PROJECT

@pytest.fixture(autouse=True)
def cleanup():
    shutil.rmtree(STAGING_ROOT, ignore_errors=True)
    mkdir(STAGING_ROOT)

def test_make_dir():
    path = STAGING_ROOT + "/test_dir"
    staging._make_dir(path)
    result = stat(path)
    assert result.st_mode == 0o41775

def test_new():
    proj = Project(**PROJECT)
    staging.new(proj)
    path = join(STAGING_ROOT, str(proj.id), proj.name)
    assert isdir(path), 'Project directory not created'
    path = join(path, proj.datasets['48a71a3e-c97c-43ea-ba41-8c2b31dd32b2'].dir_name())
    assert isdir(join(STAGING_ROOT, path)), 'Parent dataset directory not created'
    assert DatasetDirectory.select().count() == 3

def test_delete_dir():
    path = STAGING_ROOT + "/test_file_dir"
    os.mkdir(path)
    with open(f"{path}/test_file", "w") as f:
        pass
    staging._delete_dir(path)
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
    makedirs(join(STAGING_ROOT, project.id, project.name))
    project.old_name = project.name
    project.name = "new_name"
    staging.update(project)
    assert exists(join(STAGING_ROOT, project.id, project.name))

def test_update_add_datasets():
    project = TestProject()
    project.datasets_to_add = [1]
    makedirs(join(STAGING_ROOT, project.id, project.name))
    staging.update(project)
    assert exists(join(STAGING_ROOT, project.id, project.name, project.datasets[1].name))

def test_datasets_to_remove():
    project = TestProject()
    project.names_of_datasets_to_remove = ["dataset1"]
    makedirs(join(STAGING_ROOT, project.id, project.name, project.datasets[1].name))
    staging.update(project)
    assert not exists(join(STAGING_ROOT, project.id, project.name, project.datasets[1].name))

