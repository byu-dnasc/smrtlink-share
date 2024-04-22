from os import listdir, mkdir, makedirs, link, rename, stat, remove, walk, rmdir
import shutil
import peewee as pw
import app.smrtlink as smrtlink
import pwd
from os.path import join, basename, dirname, exists
import app.dataset as dataset
import app.globus as globus
from app import get_env_var

root = '/tmp/staging'
PERMISSION=0o775
APP_USER = get_env_var("APP_USER")

class DatasetDirectory(pw.Model):
    dataset_id = pw.UUIDField()
    path = pw.CharField()

def make_dir(dir):
    """
    Calls the makedirs method.
    PERMISSION gives the owner and the group full permissions. 
    exist_ok=True will prevent an error from occuring if the directory already exists. 
    """
    makedirs(dir, PERMISSION, exist_ok=True)

def stage_dataset(dir, dataset):
    """
    For each file in a dataset, the filepath is linked to the dataset directory.
    """
    for filepath in dataset.files:
        link(filepath, join(dir, basename(filepath)))

def get_user(filepath):
    return pwd.getpwuid(stat(filepath).st_uid).pw_name

def delete_dir(path):
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
            fileowner = get_user(filepath)
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
    """
    Gets called in response to a POST request. Creates directories for the project root, id, and name.
    Then creates and stages a directory for each dataset in a project's dataset_ids attribute based on the uuids.
    """
    project_dir = join(root, str(project.id), project.name)
    makedirs(project_dir)
    for uuid in project.dataset_ids:
        dataset = smrtlink.get_client().get_dataset(uuid)
        if not dataset:
            continue
        dataset_dir = join(project_dir, dataset.name)
        mkdir(dataset_dir)
        stage_dataset(dataset_dir, dataset)

def get_project_path(project):
    """
    Gets the project path by joining the root directory to the project id and project name.
    """
    project_path = join(root, project.id, project.name)
    return project_path

def rename_project(project):
    """
    Gets called in the update function below. It simply replaces the 
    old project path with the new one. 
    """
    project_path = get_project_path(project)
    old_project_path = join(dirname(project_path), project.old_name)
    rename(old_project_path, project_path)

def add_datasets(project):
    project_path = get_project_path(project)
    for dataset_id in project.datasets_to_add:
        dataset = project.datasets[dataset_id]
        project_path = get_project_path(project)
        dataset_dir = join(project_path, dataset.dir_path())
        make_dir(dataset_dir)
        DatasetDirectory.create(dataset_id=dataset_id, path=dataset_dir)
        stage_dataset(dataset_dir, dataset)

def remove_datasets(project):
    """
    Gets called in the update function below. For each dataset_id in the project.datasets_to_remove 
    attribute, the dataset path is queried and deleted.
    """
    project_path = get_project_path(project)
    for dataset_id in project.datasets_to_remove:
        dataset_path = (DatasetDirectory.select(DatasetDirectory.path)
                                        .where(DatasetDirectory.dataset_id == dataset_id))
        delete_dir(dataset_path)

def add_member(project):
    """
    Gets called in the update function below. For each member in the project.members_to_add 
    attribute, the add_access_rule function is called to grant each member an access rule.
    """
    project_path = get_project_path(project)
    for member in project.members_to_add:
        globus.add_access_rule(member, project_path, project.id)

def remove_member(project):
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
        rename_project(project)
    if hasattr(project, "datasets_to_add"):
        add_datasets(project)
    if hasattr(project, "datasets_to_remove"):
        remove_datasets(project)
    if hasattr(project, "members_to_add"):
        add_member(project)
    if hasattr(project, "members_to_remove"):
        remove_member(project)