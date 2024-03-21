import project
import smrtlink
import os

root = '/tmp/staging'

def new(project_id):
    proj = project.get(project_id)
    path = os.path.join(root, str(project_id), proj.name)
    os.makedirs(path)
    for uuid in proj.datasets.split(', '):
        dataset_dict = smrtlink.get_client().get_dataset(uuid)
        os.makedirs(os.path.join(path, dataset_dict['name']))