import os

def stage_new_project(project):
    os.makedirs(f'/mnt/smrtlink/projects/{project.name}')
    for dataset in project.datasets:
        os.makedirs(f'/mnt/smrtlink/projects/{project.name}/{dataset}')

