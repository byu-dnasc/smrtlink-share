import staging
import pytest
import os

pytestmark = pytest.mark.usefixtures('sl') # tests in this file use the SMRT Link "test client"

def test_new():
    staging.new(1)
    assert os.path.isdir("1/General Project")