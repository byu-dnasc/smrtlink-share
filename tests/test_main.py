import os
from app import globus, smrtlink
    
# Testing to see if clients did not initialize
def test_missing_clients():
    smrtlink.CLIENT = None
    

def test_missing_transfer_client():
    globus.TRANSFER_CLIENT = None
    
# Testing to see if the path to the database is valid or not
def test_path_invalid():
    invalid_file_path = '/directory/sfda'
    os.environ['DB_PATH'] = invalid_file_path
    from app import __main__
