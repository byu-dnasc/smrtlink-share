import app.smrtlink as smrtlink
from os import listdir, mkdir, makedirs, link, rename
from os.path import join, basename, dirname

root = '/tmp/staging'

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
