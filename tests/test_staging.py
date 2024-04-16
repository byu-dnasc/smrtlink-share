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

class Obj:
    def __init__ (self):
        self.id = "1"
        self.name = "test_obj"
        
def test_update_rename():
    project = Obj()
    makedirs(join(staging.root, project.id, project.name))
    project.old_name = project.name
    project.name = "new_name"
    staging.update(project)
    assert exists(join(staging.root, project.id, project.name))
