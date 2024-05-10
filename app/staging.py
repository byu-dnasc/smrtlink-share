from os import listdir, mkdir, makedirs, link, rename, stat, remove, walk, rmdir, umask
import peewee as pw
import pwd
from os.path import join, basename, dirname, exists
import app.globus as globus
from app import STAGING_ROOT, APP_USER

'''
Assumptions:
once a project is created, it will not be deleted
if a project is in the database, it 
'''

umask(0) # allow permissions to be specified explicitly
DIR_PERMISSION=0o1775 # allow group to add and remove their own files, but not delete the directory

class DatasetDirectory(pw.Model):
    dataset_id = pw.UUIDField()
    path = pw.CharField()

def _make_dir(dir):
    """
    Calls the makedirs method.
    PERMISSION gives the owner and the group full permissions. 
    exist_ok=True will prevent an error from occuring if the directory already exists. 
    """
    makedirs(dir, DIR_PERMISSION, exist_ok=True)

def _stage_dataset(dir, dataset):
    """
    For each file in a dataset, the filepath is linked to the dataset directory.
    """
    for filepath in dataset.files:
        link(filepath, join(dir, basename(filepath)))

def _get_user(filepath):
    return pwd.getpwuid(stat(filepath).st_uid).pw_name

def _delete_dir(path):
    """
    Gets called in a DELETE request. If there is one or more file(s) that belong to a different owner, it will delete 
    all other files that belong to the app and not touch the others. 
    After deleting all files belonging to the app, it tries to delete the directory that contained the files if 
    there are no other files belonging to other uses in that directory. If there are other files, that directory
    may continue to exist. 
    """
    # if all of the files in a directory belong to us, delete the whole directory, 
    # if there is one or more file(s) that belong to a specific owner, delete all 
    # other files that belong to us and leave the other ones. 
    if not exists(path):
        return
    for dirpath, dirnames, filenames in walk(path):
        for filename in filenames:
            filepath = join(dirpath, filename)
            fileowner = _get_user(filepath)
            if fileowner == APP_USER:
                remove(filepath)
    try:
        # After deleting all files that belong to the app user, to try to delete
        # the directory that contained the files if there are no other files belonging
        # to other users in that directory. If there were other files, it is okay
        # for the directory to continue to exist.
        rmdir(path)
    except:
        pass

def new(project):
    '''Raises file exceptions'''
    project_dir = join(STAGING_ROOT, project.dir_name)
    _make_dir(project_dir)
    for dataset in project.datasets:
        dataset_dir = join(project_dir, dataset.dir_name())
        _make_dir(dataset_dir)
        _stage_dataset(dataset_dir, dataset)

def _get_project_path(project):
    """
    Gets the project path by joining the root directory to the project id and project name.
    """
    project_path = join(STAGING_ROOT, project.id, project.name)
    return project_path

def _rename_project(project):
    """
    Gets called in the update function below. It simply replaces the 
    old project path with the new one. 
    """
    new_project_path = _get_project_path(project)
    current_project_path = join(dirname(new_project_path), project.old_name)
    rename(current_project_path, new_project_path)

def _add_datasets(project):
    project_path = _get_project_path(project)
    for dataset_id in project.datasets_to_add:
        dataset = project[dataset_id]
        project_path = _get_project_path(project)
        dataset_dir = join(project_path, dataset.dir_path())
        _make_dir(dataset_dir)
        DatasetDirectory.create(dataset_id=dataset_id, path=dataset_dir)
        _stage_dataset(dataset_dir, dataset)

def _remove_datasets(project):
    """
    Gets called in the update function below. For each dataset_id in the project.datasets_to_remove 
    attribute, the dataset path is queried and deleted.
    """
    for dataset_id in project.datasets_to_remove:
        dataset_path = (DatasetDirectory.select(DatasetDirectory.path)
                                        .where(DatasetDirectory.dataset_id == dataset_id))
        _delete_dir(dataset_path)

def _add_member(project):
    """
    Gets called in the update function below. For each member in the project.members_to_add 
    attribute, the add_access_rule function is called to grant each member an access rule.
    """
    project_path = _get_project_path(project)
    for member in project.members_to_add:
        globus.add_access_rule(member, project_path, project.id)

def _remove_member(project):
    """
    Gets called in the update function below. For each member in the project.members_to_remove
    attribute, the delete_access_rule function is called to remove each members' access rule.
    """
    for member in project.members_to_remove:
        globus.delete_access_rule(member, project.id)
 
def update(project):
    """
    When a PUT request is sent to the SmartLink server, this function will be called. 
    This function runs through a series of if statements to determine what kinds of updates
    need to be made to the project. Updates could be changing the name, adding or removing 
    datasets, or adding or removing members to/from the Globus collection.
    """
    if hasattr(project, "old_name"):
        _rename_project(project)
    if hasattr(project, "datasets_to_add"):
        _add_datasets(project)
    if hasattr(project, "datasets_to_remove"):
        _remove_datasets(project)
    if hasattr(project, "members_to_add"):
        _add_member(project)
    if hasattr(project, "members_to_remove"):
        _remove_member(project)