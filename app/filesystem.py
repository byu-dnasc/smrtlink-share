import pwd
import os

import app.collection
import app

os.umask(0) # allow permissions to be specified explicitly
DIR_PERMISSION=0o1775 # allow group to add and remove their own files, but not delete the directory

try:
    if not os.path.exists(app.STAGING_ROOT):
        os.mkdir(app.STAGING_ROOT, DIR_PERMISSION)
except Exception as e:
    print(f"Failed to create staging root directory: {e}")

def _make_dir(dir):
    path = os.path.join(app.STAGING_ROOT, dir)
    os.makedirs(path,
             DIR_PERMISSION, 
             exist_ok=True)
    return path

def stage(collection: app.collection.FileCollection):
    try:
        dir = _make_dir(collection.dir_path)
        for filepath in collection.files:
            os.link(filepath, os.path.join(app.STAGING_ROOT, dir, os.path.basename(filepath)))
        return True
    except Exception as e:
        app.logger.error(f'Failed to stage files: {e}')
        return False

def _get_user(filepath):
    return pwd.getpwuid(os.stat(filepath).st_uid).pw_name

def _delete_dir(path):
    if not os.path.exists(path):
        return
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            fileowner = _get_user(filepath)
            if fileowner == app.APP_USER:
                remove(filepath)
    os.rmdir(path)

def remove(dataset: app.collection.Dataset):
    try:
        dataset_dir = os.path.join(app.STAGING_ROOT, dataset.dir_path)
        _delete_dir(dataset_dir)
    except Exception as e:
        app.logger.error(f'Failed to remove dataset {dataset.id}: {e}')
        return False
    return True