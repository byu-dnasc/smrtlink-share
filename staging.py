import project
import os

def new(project_id):
    os.mkdir(str(project_id))
    name = project.get(project_id).name
    project_name = os.path.join(str(project_id), name)
    os.mkdir(project_name)