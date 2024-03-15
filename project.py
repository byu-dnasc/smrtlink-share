import peewee as pw
import smrtlink

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

def dict_to_project(dct):
    members = [member['login'] for member in dct['members']]
    dct['members'] = ', '.join(members[1:]) # ignore the first member (project owner)
    dct['datasets'] = ', '.join([dataset['uuid'] for dataset in dct['datasets']])
    return Project(**dct)

def get(id) -> Project:
    '''Returns a Project object, or None if not found.'''
    sl_client = smrtlink.get_client()
    project = sl_client.get_project_dict(id)
    if project:
        return dict_to_project(project)
    return None

class OutOfSyncError(Exception):
    pass

def get_new():
    sl_client = smrtlink.get_client()
    db_ids = Project.select(Project.id)
    sl_ids = sl_client.get_project_ids()

    offset = len(sl_ids) - len(db_ids)
    if offset == 0:
        return None
    elif offset > 1:
        raise OutOfSyncError()

    return sl_client.get_project_dict(sl_ids[-1])

def init_db(db_file):
    db = pw.SqliteDatabase(db_file)
    Project.bind(db)
    with db:
        db.create_tables([Project], safe=True)
    return db

def load_db():
    sl_client = smrtlink.get_client()
    projects = []
    for id in sl_client.get_project_ids():
        project_dict = sl_client.get_project_dict(id)
        projects.append(dict_to_project(project_dict))
    Project.bulk_create(projects)