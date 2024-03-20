import staging
import os

def test_new():
    staging.new(1)
    assert os.path.isdir("1/General Project")