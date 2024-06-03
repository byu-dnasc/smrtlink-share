from collections import defaultdict

from app import logger
from app.collection import Dataset, Parent, Child
from app.state import ProjectModel, ProjectDataset, ProjectMember

'''
SMRT Link uses parent datasets to represent a group of datasets.
When you query SMRT Link for a project's data, if a parent dataset
is in the project, then its children are not returned.
'''

def get_project_dir_name(id, name):
    return f'Project {id}: {name}'

class Project:
    '''Use to instantiate NewProject and UpdatedProject'''
    def __new__(cls, **kwargs):
        if 'id' in kwargs or 'name' in kwargs:
            if 'datasets' in kwargs and 'members' in kwargs:
                project_exists = (ProjectModel.select()
                                        .where(ProjectModel.id == kwargs['id'])
                                        .exists())
                if project_exists:
                    return super(Project, cls).__new__(UpdatedProject)
                return super(Project, cls).__new__(NewProject)
            return super(Project, cls).__new__(cls)
        raise ValueError('Missing arguments to Project.__new__')
    
    def __init__(self, **kwargs):
        '''id is a required kwarg, name is optional'''
        assert 'id' in kwargs
        self.id = str(kwargs['id'])
        if 'name' in kwargs:
            self.name = kwargs['name']
        else:
            self.name = ProjectModel.get_by_id(kwargs['id']).name
        self.dir_name = get_project_dir_name(self.id, self.name)
        
def _get_member_ids(members):
    '''Return a list of member ids from a dictionary of project data
    from SMRT Link. Exclude the project owner from the list of members.
    '''
    return [member['login']
            for member in members
            if member['role'] != 'OWNER']

def _dicts_to_datasets(dataset_dicts):
    other_datasets = []
    for ds_dct in dataset_dicts:
        try:
            other_datasets.append(Dataset(**ds_dct))
        except Exception as e:
            logger.error(f"Cannot handle SMRT Link dataset {ds_dct['id']}: {e}.")
    child_datasets = []
    for ds in other_datasets:
        if type(ds) is Parent: # then its children are not explicitly in the project
            child_datasets.extend(ds.child_datasets)
    return other_datasets + child_datasets

def _get_effects(dataset_ids):
    '''Get the union of the dataset ids in the parameter and the dataset ids
    in the database
    '''
    if not dataset_ids:
        return []
    stolen_dataset_rows = (ProjectDataset.select()
                            .where(ProjectDataset.dataset_id.in_(dataset_ids))
                            .execute())
    rows_by_project_id = defaultdict(list) # dict but any key gets a default value assigned by list()
    for row in stolen_dataset_rows:
        rows_by_project_id[row.project_id].append(row)
    # generate a list of UpdatedProject instances, one for each project from which a dataset was stolen
    for project_id in rows_by_project_id:
        project = UpdatedProject(id=project_id)
        project._datasets_to_remove = [row.dataset_id for row in rows_by_project_id[project_id]]
        project.dirs_to_remove = [row.staging_dir for row in rows_by_project_id[project_id]]
        yield project

class UpdatedProject(Project):
    '''
    An UpdatedProject includes the following attributes:
    - `old_dir_name`: the project's current directory name.
    - `new_datasets`: a list of Dataset instances for staging.
    - `dirs_to_remove`: a list of relative paths to directories used to stage
        datasets that are no longer part of the project and should be removed.
    - `new_members`: a list of member ids to share the project with.
    - `members_to_remove`: a list of member ids whose access to the project should
        be revoked.
    '''
    def _set_updates(self, **project_d):
        assert 'datasets' in project_d and 'members' in project_d
        db_project = ProjectModel.get(ProjectModel.id == int(self.id))
        if self.name != db_project.name:
            self.old_dir_name = get_project_dir_name(db_project.id, db_project.name)
        current_dataset_ids = {ds_dict['uuid'] for ds_dict in project_d['datasets']}
        stale_dataset_ids = {dataset.dataset_id for dataset in db_project.datasets}
        new_dataset_ids = list(current_dataset_ids - stale_dataset_ids)
        if new_dataset_ids:
            new_dataset_dicts = [ds_d for ds_d in project_d['datasets']
                                if ds_d['uuid'] in new_dataset_ids]
            self.new_datasets = _dicts_to_datasets(new_dataset_dicts)
        self._datasets_to_remove = list(stale_dataset_ids - current_dataset_ids)
        if self._datasets_to_remove:
            self.dirs_to_remove = [dataset.staging_dir 
                                   for dataset in db_project.datasets
                                   if dataset.dataset_id in self._datasets_to_remove]
        current_members = set(_get_member_ids(project_d['members']))
        stale_members = set(db_project.member_ids)
        if current_members - stale_members:
            self.members_to_add = list(current_members - stale_members)
        if stale_members - current_members:
            self.members_to_remove = list(stale_members - current_members)

    def __init__(self, **kwargs):
        self.old_dir_name = None
        self.new_datasets = []
        self.dirs_to_remove = []
        self.new_members = []
        self.members_to_remove = []
        if 'name' in kwargs: # use instance to handle a project update
            super().__init__(**kwargs)
            self._set_updates(**kwargs)
            self.effects = _get_effects([ds.id for ds in self.new_datasets if isinstance(ds, Dataset)])
        else: # use instance to handle stolen datasets
            super().__init__(id=kwargs['id'])

    def save(self):
        if self.old_dir_name:
            (ProjectModel.update(name=self.name)
                        .where(ProjectModel.id == self.id)
                        .execute())
        if self.new_datasets:
            for dataset in self.new_datasets:
                if type(dataset) is Dataset or \
                   type(dataset) is Parent:
                    (ProjectDataset.insert(project_id=self.id, 
                                        dataset_id=dataset.id,
                                        staging_dir=dataset.dir_path)
                                    .execute())
        if self._datasets_to_remove:
            (ProjectDataset.delete()
                            .where(ProjectDataset.project_id == self.id,
                                   ProjectDataset.dataset_id.in_(self._datasets_to_remove))
                            .execute())
        if self.new_members:
            for member in self.new_members:
                ProjectMember.insert(project_id=self.id, member_id=member).execute()
        if self.members_to_remove:
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
        '''
        super().__init__(**project_d)
        assert 'datasets' in project_d and 'members' in project_d
        self.datasets = _dicts_to_datasets(project_d['datasets'])
        self.members = _get_member_ids(project_d['members'])
        self.effects = _get_effects([ds.id for ds in self.datasets if isinstance(ds, Dataset)])

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
        dataset_rows = [{'project_id': self.id, 
                         'dataset_id': ds.id,
                         'staging_dir': ds.dir_path}
                         for ds in self.datasets
                         if type(ds) is Dataset or \
                            type(ds) is Parent]
        ProjectDataset.insert_many(dataset_rows).execute()
        member_rows = [{'project_id': self.id,
                        'member_id': member} 
                        for member in self.members]
        ProjectMember.insert_many(member_rows).execute()

    def __iter__(self):
        '''Iterate over datasets in the project.'''
        return iter(self.datasets)