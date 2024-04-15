import app.smrtlink as smrtlink
from os import listdir, mkdir, makedirs, link, rename, stat, remove, walk
import pwd
from os.path import join, basename, dirname, exists
import shutil
import app.globus
from app import get_env_var

root = '/tmp/staging'
PERMISSION=0o775
APP_USER = get_env_var("APP_USER")

def make_dir(dir):
    mkdir(dir, PERMISSION)

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

def update(project):
    project_path = join(root, project.id, project.name)
    if hasattr(project, "rename"):
        new_project_path = join(dirname(project_path), project.name)
        rename(project_path, new_project_path)
    if hasattr(project, "datasets_to_add"):
        for dataset_id in project.datasets_to_add:
            dataset = project.datasets[dataset_id]
            dataset_dir = join(project_path, dataset.name)
            make_dir(dataset_dir)
            stage_dataset(dataset_dir, dataset)
    if hasattr(project, "datasets_to_remove"):
        for dataset in project.datasets_to_remove:
            dataset = project.datasets[dataset_id]
            dataset_path = join(project_path, dataset.name)
            delete_dir(dataset_path)
    if hasattr(project, "members_to_add"):
        for member in project.members_to_add:
            globus.add_access_rule(member, project_path, project.id)
    if hasattr(project, "members_to_remove"):
        for member in project.members_to_remove:
            globus.delete_access_rule(member, project.id)