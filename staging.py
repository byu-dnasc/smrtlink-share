import project
import os

def new(project_id):
    os.mkdir(project_id)
    name = project.get(project_id).name
    project_name = os.path.join(project_id, name)
    os.mkdir(project_name)