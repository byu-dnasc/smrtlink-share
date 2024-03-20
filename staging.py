import project
import os

def new(projectID):
    os.mkdir(projectID)
    name = project.get(projectID).name
    projectName = os.path.join(projectID, name)
    os.mkdir(projectName)