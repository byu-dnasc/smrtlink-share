import project
import os

def new(projectID):
    os.mkdir(projectID)
    projectInfo = project.get(projectID)
    name = projectInfo.name
    projectName = os.path.join(projectID, name)
    os.mkdir(projectName)