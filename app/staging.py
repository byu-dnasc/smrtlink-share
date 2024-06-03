from os import makedirs, link, rename, stat, remove, walk, rmdir, umask
import pwd
from os.path import join, basename, exists
from app import STAGING_ROOT, APP_USER, logger
from app.project import UpdatedProject

umask(0) # allow permissions to be specified explicitly
DIR_PERMISSION=0o1775 # allow group to add and remove their own files, but not delete the directory

def _make_dir(dir):
    makedirs(join(STAGING_ROOT, dir), 
             DIR_PERMISSION, 
             exist_ok=True)

def _stage_dataset(dir, dataset):
    for filepath in dataset.files:
        link(filepath, join(STAGING_ROOT, dir, basename(filepath)))

def _get_user(filepath):
    return pwd.getpwuid(stat(filepath).st_uid).pw_name

def _delete_dir(path):
    if not exists(path):
        return
    for dirpath, dirnames, filenames in walk(path):
        for filename in filenames:
            filepath = join(dirpath, filename)
            fileowner = _get_user(filepath)
            if fileowner == APP_USER:
                remove(filepath)
    rmdir(path)

def _rename_project(project):
    current_project_path = join(STAGING_ROOT, project.old_dir_name)
    new_project_path = join(STAGING_ROOT, project.dir_name)
    rename(current_project_path, new_project_path)

def _add_datasets(project):
    for dataset in project.datasets_to_add:
        dataset_dir = join(project.dir_name, dataset.dir_path)
        _make_dir(dataset_dir)
        _stage_dataset(dataset_dir, dataset)

def _remove_dataset_dirs(project):
    for dataset_path in project.dirs_to_remove:
        _delete_dir(dataset_path)

def update(project: UpdatedProject):
    if project.old_dir_name:
        try:
            _rename_project(project)
        except Exception as e:
            logger.error(f'Failed to rename project {project.id}: {e}')
    if project.new_datasets:
        try:
            _add_datasets(project)
        except Exception as e:
            logger.error(f'Failed to create new dataset files: {e}')
    if project.dirs_to_remove:
        try:
            _remove_dataset_dirs(project)
        except Exception as e:
            logger.error(f'Failed to remove dataset files: {e}')

def new(project):
    _make_dir(project.dir_name)
    for dataset in project.datasets:
        dataset_dir = join(project.dir_name, dataset.dir_name)
        _make_dir(dataset_dir)
        _stage_dataset(dataset_dir, dataset)

def analysis(project, analysis):
    try:
        analysis_dir = join(project.dir_name, analysis.dir_name)
        _stage_dataset(analysis_dir, analysis)
    except Exception as e:
        logger.error(f'Failed to create analysis files: {e}')