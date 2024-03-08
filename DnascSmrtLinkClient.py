from smrtlink_client import SmrtLinkClient

class DnascSmrtLinkClient(SmrtLinkClient):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
    
    def get_project(self, id):
        """Retrieve a list of projects"""
        # TODO: handle case where project does not exist (for handling POST request)
        return self.get(f"/smrt-link/projects/{id}")
    
    @staticmethod
    def connect():
        return DnascSmrtLinkClient(
            host="localhost",
            port=8243,
            username="admin",
            password="admin",
            verify=False # Disable SSL verification (optional, default is True, i.e. SSL verification is enabled)
        )