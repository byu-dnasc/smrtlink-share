from smrtlink_client import SmrtLinkClient

class DnascSmrtLinkClient(SmrtLinkClient):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
    
    def get_project(self, id):
        """Retrieve a list of projects"""
        j = self.get(f"/smrt-link/projects/{id}")
        p = Project.from_json(j)
        return p
    
    @staticmethod
    def connect():
        return DnascSmrtLinkClient(
            host="localhost",
            port=8243,
            username="admin",
            password="admin",
            verify=False # Disable SSL verification (optional, default is True, i.e. SSL verification is enabled)
        )


class Project:
    def __init__(self, name, updated_at, state, description, datasets, id, created_at, is_active, members):
        self.name = name
        self.updated_at = updated_at
        self.state = state
        self.description = description
        self.datasets = datasets
        self.id = id
        self.created_at = created_at
        self.is_active = is_active
        self.members = members

    @classmethod
    def from_json(cls, json_data):
        name = json_data.get("name")
        updated_at = json_data.get("updatedAt")
        state = json_data.get("state")
        description = json_data.get("description")
        datasets = json_data.get("datasets", [])
        id = json_data.get("id")
        created_at = json_data.get("createdAt")
        is_active = json_data.get("isActive")
        members = json_data.get("members", [])
        
        # Parse members list
        parsed_members = [{"login": member["login"], "role": member["role"]} for member in members]

        return cls(name, updated_at, state, description, datasets, id, created_at, is_active, parsed_members)

    def __str__(self):
        return f"Project: {self.name}, ID: {self.id}, State: {self.state}"