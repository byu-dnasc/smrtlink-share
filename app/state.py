import peewee
import app

try:
    db = peewee.SqliteDatabase(app.DB_PATH)
except Exception as e:
    raise ImportError(f"Failed to initialize database: {e}")

class AppState(peewee.Model):
    '''Subclass of `peewee.Model` that sets the database to the global `db` variable.'''
    class Meta:
        database = db

class Dataset(AppState):
    id = peewee.CharField(primary_key=True, 
                      max_length=36)
    project_id = peewee.IntegerField()
    dir_path = peewee.CharField()

class ProjectMember(AppState):
    project_id = peewee.IntegerField()
    member_id = peewee.CharField()

class Permission(AppState):
    id = peewee.CharField(primary_key=True)
    member_id = peewee.CharField()
    dataset_id = peewee.CharField()

class Job(AppState):
    id = peewee.IntegerField(primary_key=True)

class LastJobUpdate(AppState):
    '''
    A class defining a table with a single row which stores a timestamp.
    '''
    timestamp = peewee.DateTimeField()

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

db.create_tables([Dataset, 
                  ProjectMember,
                  LastJobUpdate], 
                  safe=True)
LastJobUpdate.create(timestamp='2000-01-01T00:00:00.000Z')