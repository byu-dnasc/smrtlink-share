import peewee as pw
from app import DB_PATH

try:
    db = pw.SqliteDatabase(DB_PATH)
except Exception as e:
    raise ImportError(f"Failed to initialize database: {e}")

class AppModel(pw.Model):
    class Meta:
        database = db

class ProjectModel(AppModel):

    id = pw.IntegerField(primary_key=True)
    name = pw.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert hasattr(self, 'datasets'), 'ProjectDataset foreign key backref not found'
        assert hasattr(self, '_members'), 'ProjectMember foreign key backref not found'
        self.member_ids = [str(record.member_id) for record in self._members]
    
class ProjectDataset(AppModel):
    project_id = pw.ForeignKeyField(ProjectModel, backref='datasets')
    dataset_id = pw.CharField(max_length=50)
    staging_dir = pw.CharField()

class ProjectMember(AppModel):
    project_id = pw.ForeignKeyField(ProjectModel, backref='_members')
    member_id = pw.CharField()

class AnalysisModel(AppModel):
    project_id = pw.IntegerField()
    dataset_id = pw.CharField(max_length=50)
    analysis_id = pw.IntegerField

class LastJobUpdate(AppModel):
    '''
    A class defining a table with a single row which stores a timestamp.
    '''
    timestamp = pw.DateTimeField()

    @staticmethod
    def set(time):
        '''
        Update the value of `timestamp`.

        `time`: the `createdAt` timestamp of the latest job (by `createdAt`) 
        seen by the app.
        '''
        LastJobUpdate.update(timestamp=time).execute()

    @staticmethod
    def time():
        '''
        Get the `createdAt` timestamp of the latest job handled by the app.
        Would have called it `get`, but I don't want to override the built-in.
        '''
        return LastJobUpdate.get_by_id(1).timestamp

db.create_tables([ProjectModel,
                    ProjectDataset, 
                    ProjectMember,
                    LastJobUpdate], 
                    safe=True)
LastJobUpdate.create(timestamp='2000-01-01T00:00:00.000Z')