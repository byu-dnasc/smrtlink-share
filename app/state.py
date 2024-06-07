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

class Dataset(AppState, app.BaseDataset):
    id = peewee.CharField(primary_key=True, 
                      max_length=36)
    project_id = peewee.IntegerField()
    dir_path = peewee.CharField()

    @property
    def uuid(self):
        return self.id

    @staticmethod
    def add(project_id, dataset):
        (Dataset.insert(project_id=project_id,
                        id=dataset.id,
                        dir_path=dataset.dir_path)
                .execute())
    
    @staticmethod
    def get_one(id: str) -> 'Dataset' | None:
        return Dataset.get_or_none(Dataset.id == id)
    
    @staticmethod
    def get_multiple(project_id: int) -> list['Dataset']:
        return (Dataset.select()
                       .where(Dataset.project_id == project_id)
                       .execute())
    
    @staticmethod
    def get_previous_datasets(project_id, current_datasets):
        return (Dataset
                .select()
                .where(Dataset.project_id == project_id,
                       Dataset.id.not_in(current_datasets))
                .execute())

class ProjectMember(AppState):
    project_id = peewee.IntegerField()
    member_id = peewee.CharField()

    @staticmethod
    def add(project_id: int, member_id: str):
        ProjectMember.insert(project_id=project_id,
                             member_id=member_id).execute()

    @staticmethod
    def get_one(project_id: int, member_id: str) -> 'ProjectMember' | None:
        return ProjectMember.get_or_none(ProjectMember.project_id == project_id,
                                         ProjectMember.member_id == member_id)

    @staticmethod
    def get_previous_members(project_id, current_members):
        return (ProjectMember
                .select()
                .where(ProjectMember.project_id == project_id,
                       ProjectMember.member_id.not_in(current_members))
                .execute())

class Permission(AppState):
    id = peewee.CharField(primary_key=True)
    member_id = peewee.CharField()
    dataset_id = peewee.CharField()

    @staticmethod
    def add(id, member_id, dataset_id):
        Permission.insert(id=id,
                          member_id=member_id,
                          dataset_id=dataset_id).execute()
    
    @staticmethod
    def get_one(member_id, dataset_id):
        return Permission.get_or_none(Permission.member_id == member_id,
                                      Permission.dataset_id == dataset_id)
    
    @staticmethod
    def get_multiple(dataset_id):
        return (Permission.select()
                          .where(Permission.dataset_id == dataset_id)
                          .execute())

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
                  Permission,
                  LastJobUpdate], 
                  safe=True)
LastJobUpdate.create(timestamp='2000-01-01T00:00:00.000Z')