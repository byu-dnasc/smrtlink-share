import staging
import shutil
import pytest
import os

pytestmark = pytest.mark.usefixtures('sl') # tests in this file use the SMRT Link "test client"

@pytest.fixture(autouse=True)
def cleanup():
    shutil.rmtree(staging.root, ignore_errors=True)

def test_new():
    staging.new(2)
    assert os.path.isdir(os.path.join(staging.root, "2/Tomato"))