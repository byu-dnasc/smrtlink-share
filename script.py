from DnascSmrtLinkClient import DnascSmrtLinkClient, Project
import json

client = DnascSmrtLinkClient.connect()
project = client.get_project(2)

print(json.dumps(project,indent=4))

p = Project.from_json(project)
print(p)