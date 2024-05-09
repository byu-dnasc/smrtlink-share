import peewee as pw
from app import db
from app.dataset import Dataset, Parent, Child

'''
SMRT Link uses parent datasets to represent a group of datasets.
When you query SMRT Link for a project's data, if a parent dataset
is in the project, then its children are not returned.
'''

class ProjectModel(pw.Model):

    id = pw.IntegerField(primary_key=True)
    name = pw.CharField()

    class Meta:
        database = db
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert hasattr(self, 'datasets'), 'ProjectDataset foreign key backref not found'
        assert hasattr(self, '_members'), 'ProjectMember foreign key backref not found'
        self.member_ids = [str(record.member_id) for record in self._members]
    
class ProjectDataset(pw.Model):
    class Meta:
        database = db
    project_id = pw.ForeignKeyField(ProjectModel, backref='datasets')
    dataset_id = pw.UUIDField()
    staging_dir = pw.CharField()

class ProjectMember(pw.Model):
    class Meta:
        database = db
    project_id = pw.ForeignKeyField(ProjectModel, backref='_members')
    member_id = pw.CharField()

class Project:
    '''Use to instantiate NewProject and UpdatedProject'''
    def __new__(cls, **project_d):
        if 'datasets' in project_d and 'members' in project_d:
            if not 'id' in project_d or not 'name' in project_d:
                raise ValueError('Missing arguments to Project.__new__')
            project_exists = (ProjectModel.select()
                                    .where(ProjectModel.id == project_d['id'])
                                    .exists())
            if project_exists:
                return super(Project, cls).__new__(UpdatedProject)
            return super(Project, cls).__new__(NewProject)
        else:
            raise ValueError('Missing arguments to Project.__new__')
    
    def __init__(self, id, name):
        self.id = str(id)
        self.name = name
        
def get_member_ids(project_d):
    '''Return a list of member ids from a dictionary of project data
    from SMRT Link. Exclude the project owner from the list of members.
    '''
    return [member['login']
            for member in project_d['members'] 
            if member['role'] != 'OWNER']

class UpdatedProject(Project):
    '''
    An UpdatedProject may optionally include each of the following attributes:
    - `old_name`: the project's previous name.
    - `datasets_to_add`: a list of Dataset instances for staging.
    - `dirs_to_remove`: a list of relative paths to directories used to stage
        datasets that are no longer part of the project and should be removed.
    - `members_to_add`: a list of member ids to share the project with.
    - `members_to_remove`: a list of member ids whose access to the project should
        be revoked.
    '''
    def __init__(self, **project_d):
        super().__init__(project_d['id'], project_d['name'])
        # Identify changes between the instance and the database.
        db_project = ProjectModel.get(ProjectModel.id == int(self.id))
        if self.name != db_project.name:
            self.old_name = db_project.name
        current_dataset_ids = {ds_dict['uuid'] for ds_dict in project_d['datasets']}
        stale_dataset_ids = {dataset.dataset_id for dataset in db_project.datasets}
        new_dataset_ids = list(current_dataset_ids - stale_dataset_ids)
        if new_dataset_ids:
            self.datasets_to_add = [Dataset(**ds_dict)
                                    for ds_dict in project_d['datasets']
                                    if ds_dict['uuid'] in new_dataset_ids]
        self._datasets_to_remove = list(stale_dataset_ids - current_dataset_ids)
        if self._datasets_to_remove:
            self.dirs_to_remove = [dataset.staging_dir 
                                   for dataset in db_project.datasets
                                   if dataset.dataset_id in self._datasets_to_remove]
        current_members = set(get_member_ids(project_d))
        stale_members = set(db_project.member_ids)
        if current_members - stale_members:
            self.members_to_add = list(current_members - stale_members)
        if stale_members - current_members:
            self.members_to_remove = list(stale_members - current_members)

    def save(self):
        if hasattr(self, 'old_name'):
            (ProjectModel.update(name=self.name)
                        .where(ProjectModel.id == self.id)
                        .execute())
        if hasattr(self, 'datasets_to_add'):
            for dataset in self.datasets_to_add:
                (ProjectDataset.insert(project_id=self.id, 
                                      dataset_id=dataset.id,
                                      staging_dir=dataset.dir_name())
                               .execute())
        if hasattr(self, '_datasets_to_remove'):
            (ProjectDataset.delete()
                            .where(ProjectDataset.project_id == self.id,
                                   ProjectDataset.dataset_id.in_(self._datasets_to_remove))
                            .execute())
        if hasattr(self, 'members_to_add'):
            for member in self.members_to_add:
                ProjectMember.insert(project_id=self.id, member_id=member).execute()
        if hasattr(self, 'members_to_remove'):
            (ProjectMember.delete()
                           .where(ProjectMember.project_id == self.id,
                                  ProjectMember.member_id.in_(self.members_to_remove))
                           .execute())
        
class NewProject(Project):
    '''
    A NewProject includes the following attributes:
    - `datasets`: a list of Dataset instances for staging
    - `members`: a list of member ids to share the project with
    '''
    def __init__(self, **project_d):
        '''
        Initialize a NewProject instance using project data from SMRT Link.

        Note that here, a child dataset is considered a dataset whose parent
        is in the project. This implies that a project may have a dataset 
        whose parent is not in the project, but that the dataset will not be 
        represented by an instance of Dataset, not of Child. In other words,
        a child is only a child if its parent is in the project.
        '''
        super().__init__(project_d['id'], project_d['name'])
        self._other_datasets = [Dataset(**ds_dct) for ds_dct in project_d['datasets']]
        self._child_datasets = []
        for ds in self._other_datasets:
            if type(ds) is Parent:
                self._child_datasets.extend(ds.child_datasets)
        self.datasets = self._other_datasets + self._child_datasets
        self.members = get_member_ids(project_d)

    def save(self):
        '''
        Insert a new project into the database.

        Note that child datasets are not inserted into the database
        (unless their parent is not in the project, in which case
        the dataset is not considered to be a child and therefore
        recieves no special treatment).
        '''
        (ProjectModel.insert(id=int(self.id), name=self.name)
                    .execute())
        # do not insert child datasets into the database
        dataset_rows = [{'project_id': self.id, 
                         'dataset_id': ds.id,
                         'staging_dir': ds.dir_name()}
                         for ds in self._other_datasets]
        ProjectDataset.insert_many(dataset_rows).execute()
        member_rows = [{'project_id': self.id,
                        'member_id': member} 
                        for member in self.members]
        ProjectMember.insert_many(member_rows).execute()

    def __iter__(self):
        '''Iterate over datasets in the project.'''
        return iter(self.datasets)