import app.staging as staging
import shutil
import pytest
import os
import app.smrtlink as smrtlink


@pytest.fixture(autouse=True)
def cleanup():
    shutil.rmtree(staging.root, ignore_errors=True)
    os.mkdir(staging.root)

def test_new():
    staging.new(2)
    assert os.path.isdir(os.path.join(staging.root, "2/Tomato", "Germany tomato 20 and 21-Cell1 (all samples)"))

def test_delete_dir():
    path = staging.root + "/test_file_dir"
    os.mkdir(path)
    with open(f"{path}/test_file", "w") as f:
        pass
    staging.delete_dir(path)