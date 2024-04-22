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

def make_dir(dir):
    mkdir(dir, PERMISSION)

class DatasetDirectory(pw.Model):
    dataset_id = pw.UUIDField()
    path = pw.CharField()

def stage_dataset(dir, dataset):
    if dataset.is_super: # type(files) is dict
        for sample_dir_basename, filepaths in dataset.files.items():
            sample_dir = join(dir, sample_dir_basename)
            mkdir(sample_dir)
            for filepath in filepaths:
                link(filepath, join(sample_dir, basename(filepath)))
    else: # type(files) is list
        for filepath in dataset.files:
            link(filepath, join(dir, basename(filepath)))

def get_user(filepath):
    return pwd.getpwuid(stat(filepath).st_uid).pw_name

def delete_dir(path):
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
        # After deleting all files that belong to the app user, we want to try to delete
        # the directory that contained the files if there are no other files belonging
        # to other users in that directory. If there were other files, it is okay
        # for the directory to continue to exist.
        rmdir(path)
    except:
        pass

def new(project):
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
    project_path = join(root, project.id, project.name)
    return project_path

def rename_project(project):
    project_path = get_project_path(project)
    old_project_path = join(dirname(project_path), project.old_name)
    rename(old_project_path, project_path)

def add_datasets(project):
    project_path = get_project_path(project)
    for dataset_id in project.datasets_to_add:
        dataset = project.datasets[dataset_id]
        dataset_dir = dir_path(project_path, dataset)
        make_dir(dataset_dir)
        stage_dataset(dataset_dir, dataset)

def remove_datasets(project):
    project_path = get_project_path(project)
    for dataset_id in project.datasets_to_remove:
        dataset_path = (DatasetDirectory.select(DatasetDirectory.path)
                                        .where(DatasetDirectory.dataset_id == dataset_id))
        delete_dir(dataset_path)

def add_member(project):
    project_path = get_project_path(project)
    for member in project.members_to_add:
        globus.add_access_rule(member, project_path, project.id)

def remove_member(project):
    for member in project.members_to_remove:
        globus.delete_access_rule(member, project.id)
 
def update(project):
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