import datetime
import peewee
import app

try:
    db = peewee.SqliteDatabase(app.DB_PATH)
except Exception as e:
    raise ImportError(f"Failed to initialize database: {e}")

class BaseMeta(peewee.Model.__class__, app.BaseDataset.__class__):
    '''Using this metaclass prevents a metaclass conflict which would prevent
    a class like app.state.Dataset from inheriting from both peewee.Model 
    and app.BaseDataset.'''
    pass

class Dataset(peewee.Model, app.BaseDataset, metaclass=BaseMeta):
    uuid = peewee.CharField(primary_key=True, 
                        max_length=36)
    project_id = peewee.IntegerField()
    dir_path = peewee.CharField()

    @staticmethod
    def add(project_id: int, dataset: app.BaseDataset):
        (Dataset.insert(project_id=project_id,
                        uuid=dataset.uuid,
                        dir_path=dataset.dir_path)
                .execute())
    
    @staticmethod
    def where_dataset_uuid(uuid: str) -> 'Dataset' or None:
        return Dataset.get_or_none(Dataset.uuid == uuid)
    
    @staticmethod
    def where_project_id(project_id: int) -> list['Dataset']:
        return (Dataset.select()
                       .where(Dataset.project_id == project_id)
                       .execute())
    
    @staticmethod
    def get_previous_datasets(project_id: int, current_datasets: list[str]) -> list['Dataset']:
        return (Dataset
                .select()
                .where(Dataset.project_id == project_id,
                       Dataset.uuid.not_in(current_datasets))
                .execute())
    
    def update_project_id(self, project_id: int):
        self.project_id = project_id
        self.save()

class ProjectMember(peewee.Model):
    project_id = peewee.IntegerField()
    member_id = peewee.CharField()

    @staticmethod
    def add(project_id: int, member_id: str):
        ProjectMember.insert(project_id=project_id,
                             member_id=member_id).execute()
   
    @staticmethod
    def exists(project_id: int, member_id: str) -> bool:
        return (ProjectMember.select()
                            .where(ProjectMember.project_id == project_id,
                                   ProjectMember.member_id == member_id)
                            .exists())

    @staticmethod
    def get_previous_members(project_id: int, current_members: list[str]) -> list['ProjectMember']:
        return (ProjectMember
                .select()
                .where(ProjectMember.project_id == project_id,
                       ProjectMember.member_id.not_in(current_members))
                .execute())

class Permission(peewee.Model):
    id = peewee.CharField(primary_key=True)
    member_id = peewee.CharField()
    dataset_id = peewee.CharField()
    expiry = peewee.DateTimeField()

    @staticmethod
    def where(member_id: str, dataset_id: str) -> 'Permission' or None:
        return Permission.get_or_none(Permission.member_id == member_id,
                                      Permission.dataset_id == dataset_id)
    
    @staticmethod
    def where_dataset_id(dataset_id: str) -> list['Permission']:
        return (Permission.select()
                          .where(Permission.dataset_id == dataset_id)
                          .execute())
    
    @staticmethod
    def remove_expired():
        now = datetime.datetime.now()
        (Permission.delete()
                    .where(Permission.expiry < now)
                    .execute())

class LastJobUpdate(peewee.Model):
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
    def time() -> str:
        '''
        Get the `createdAt` timestamp of the latest job handled by the app.
        '''
        return LastJobUpdate.get_by_id(1).timestamp


models = [Dataset, ProjectMember, Permission, LastJobUpdate]
db.bind(models)
db.create_tables(models, safe=True)
LastJobUpdate.create(timestamp='2000-01-01T00:00:00.000Z')