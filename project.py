from requests import HTTPError
from smrtlink_client import SmrtLinkClient
import peewee as pw

class Project(pw.Model):
    # camel case for convenience in converting to/from JSON
    id = pw.IntegerField(primary_key=True)
    name = pw.CharField()
    state = pw.CharField()
    members = pw.CharField()
    datasets = pw.CharField()
    isActive = pw.BooleanField()
    createdAt = pw.CharField()
    updatedAt = pw.CharField()
    description = pw.CharField()

    def __str__(self):
        return str(self.name)

class DnascSmrtLinkClient(SmrtLinkClient):

    def get_project_dict(self, id):
        '''
        Returns a dictionary of project data, or None if not found.
        Dictionary includes lists of project datasets and members.
        '''
        try:
            return self.get(f"/smrt-link/projects/{id}")
        except HTTPError as e:
            assert e.response.status_code == 404, 'Unexpected error when getting project from SMRT Link'
            return None
    
    def get_project_dicts(self):
        '''
        Returns a list of dictionaries of project data.
        Individual project data does not include datasets or members.
        '''
        lst = self.get("/smrt-link/projects")
        projects = []
        for dct in lst:
            projects.append(dct)
        return projects
        
    @staticmethod
    def connect():
        '''Returns SmrtLinkClient, or exits if cannot connect'''
        try:
            return DnascSmrtLinkClient(
                host="localhost",
                port=8243,
                username="admin",
                password="admin",
                verify=False # Disable SSL verification (optional, default is True, i.e. SSL verification is enabled)
            )
        except Exception as e:
            print(e)
            exit(1)

    @staticmethod 
    def get_instance(): 
        if not hasattr(DnascSmrtLinkClient, "_instance"): 
            DnascSmrtLinkClient._instance = DnascSmrtLinkClient.connect() 
        return DnascSmrtLinkClient._instance

def dict_to_project(dct):
    members = [member['login'] for member in dct['members']]
    dct['members'] = ', '.join(members[1:]) # ignore the first member (project owner)
    dct['datasets'] = ', '.join([dataset['uuid'] for dataset in dct['datasets']])
    return Project(**dct)

def get(id) -> Project:
    '''Returns a Project object, or None if not found.'''
    sl_client = DnascSmrtLinkClient.get_instance()
    project = sl_client.get_project_dict(id)
    if project:
        return dict_to_project(project)
    return None

def init_db(db_file):
    db = pw.SqliteDatabase(db_file)
    Project.bind(db)
    with db:
        db.create_tables([Project], safe=True)
    return db

def get_project_ids():
    sl_client = DnascSmrtLinkClient.get_instance()
    return [project['id'] for project in sl_client.get_project_dicts()]

def load_db():
    sl_client = DnascSmrtLinkClient.get_instance()
    projects = []
    for id in get_project_ids():
        project_dict = sl_client.get_project_dict(id)
        projects.append(dict_to_project(project_dict))
    Project.bulk_create(projects)