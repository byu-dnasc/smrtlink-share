import smrtlink
import os

root = '/tmp/staging'

def stage_dataset(dir, dataset):
    if dataset.is_super: # type(files) is dict
        for sample_dir_basename, filepaths in dataset.files.items():
            sample_dir = os.path.join(dir, sample_dir_basename)
            os.mkdir(sample_dir)
            for filepath in filepaths:
                os.link(filepath, os.path.join(sample_dir, os.path.basename(filepath)))
    else: # type(files) is list
        for filepath in dataset.files:
            os.link(filepath, os.path.join(dir, os.path.basename(filepath)))

def new(project):
    project_dir = os.path.join(root, str(project.id), project.name)
    os.makedirs(project_dir)
    for uuid in project.dataset_ids:
        dataset = smrtlink.get_client().get_dataset(uuid)
        if not dataset:
            continue
        dataset_dir = os.path.join(project_dir, dataset.name)
        os.mkdir(dataset_dir)
        stage_dataset(dataset_dir, dataset)