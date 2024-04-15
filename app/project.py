import peewee as pw

class Project(pw.Model):
    '''
    Class to merely represent project data, not to modify it. 
    Unless you are `DnascSmrtLinkClient.get_project()`, do not instantiate 
    this class.

    This class also defines a database schema for project data.
    `DnascSmrtLinkClient` uses this database to identify project data
    from SMRT Link which has been updated since the last time the app
    checked.

    Therefore, data found in this class only ever flows in one direction:
    SMRT Link -> `Project` instance -> Database
    '''
    id = pw.IntegerField(primary_key=True)
    name = pw.CharField()

    def _get_updates(self, db_project):
        '''Identify changes between the instance and the database.'''
        if self.name != db_project.name:
            self.rename = True
        current_ids = {ds.uuid for ds in self.datasets}
        stale_ids = set(db_project._dataset_ids)
        if current_ids - stale_ids:
            self.datasets_to_add = list(current_ids - stale_ids)
        if stale_ids - current_ids:
            self.datasets_to_remove = list(stale_ids - current_ids)
        current_members = set(self.members)
        stale_members = set(db_project._members)
        if current_members - stale_members:
            self.members_to_add = list(current_members - stale_members)
        if stale_members - current_members:
            self.members_to_remove = list(stale_members - current_members)

    def _update_db(self):
        '''Add or remove datasets and members from the database.'''
        self.save() # update project name
        if hasattr(self, 'datasets_to_add'):
            for uuid in self.datasets_to_add:
                ProjectDataset.insert(project_id=self.id, dataset_id=uuid).execute()
        if hasattr(self, 'datasets_to_remove'):
            (ProjectDataset.delete()
                            .where(ProjectDataset.project_id == self.id,
                                   ProjectDataset.dataset_id.in_(self.datasets_to_remove))
                            .execute())
        if hasattr(self, 'members_to_add'):
            for member in self.members_to_add:
                ProjectMember.insert(project_id=self.id, member_id=member).execute()
        if hasattr(self, 'members_to_remove'):
            (ProjectMember.delete()
                           .where(ProjectMember.project_id == self.id,
                                  ProjectMember.member_id.in_(self.members_to_remove))
                           .execute())
    
    def _insert_db(self):
        '''Insert a new project into the database.'''
        self.save(force_insert=True)
        dataset_rows = [{'project_id': self.id, 
                         'dataset_id': ds.uuid} 
                         for ds in self.datasets]
        ProjectDataset.insert_many(dataset_rows).execute()
        member_rows = [{'project_id': self.id,
                        'member_id': member} 
                        for member in self.members]
        ProjectMember.insert_many(member_rows).execute()

    def __init__(self, *args, **kwargs):
        '''
        There are two types of `Project` instances, internal and external,
        whose initialization is handled respectively by one or the other
        of the two branches of this method.
        Both types of instances have a variable for each of the `peewee` 
        'fields'. These are initialized by `super().__init__()`. Both types of 
        instances also have a list of dataset ids, initialized by this method.
        The 'internal' type of instance has only the variables mentioned above
        and should only be used within `Project.__init__`.
        The 'external' type of instance has one more optional variable called
        `updates`, which is a list of field names that have changed since the 
        last time the app checked SMRT Link for updates. If the project is new
        (i.e., it does not exist in the database), then `updates` is omitted.

        Another key difference between the two types of instances is that the
        internal instance is populated with data from the database, while the
        external instance is populated with data from SMRT Link. 
        
        The instantiation of an external instance immediately saves a project
        to the database.

        :param kwargs: when using init directly (as in `smrtlink._dict_to_project`),
        `kwargs` is a dictionary of project data from SMRT Link, as well as a list 
        of dataset ids under the key 'dataset_ids'.
        '''
        if kwargs: # external instance
            # initialize instance data
            super().__init__(*args, **kwargs)
            self.datasets = [Dataset(**dct) 
                             for dct in kwargs['datasets']]
            self.members = [member['login'] 
                            for member in kwargs['members'] 
                            if member['role'] != 'OWNER']
            # compare instance data with database data
            db_project = Project.get_or_none(Project.id == self.id)
            if db_project: # get updates using database
                self._get_updates(db_project)
                self._update_db()
            else: # load new project data into database
                self._insert_db()
        else: # internal instance
            super().__init__(*args, **kwargs) # populate instance with database data in kwargs
            assert hasattr(self, '_dataset_id_refs'), 'ProjectDataset foreign key backref not found'
            assert hasattr(self, '_member_refs'), 'ProjectMember foreign key backref not found'
            self._dataset_ids = [str(ref.dataset_id) for ref in self._dataset_id_refs]
            self._members = [str(ref.member_id) for ref in self._member_id_refs]
    
    def __str__(self):
        return str(self.name)

class Dataset:
    def __init__(self, **kwargs):
        self.uuid = kwargs['uuid']
        self.name = kwargs['name']
        self.path = kwargs['path']
        self.num_children = kwargs['numChildren']

    def __str__(self):
        return str(self.name)

class ProjectDataset(pw.Model):
    '''Do not instantiate outside of `Project`.'''
    project_id = pw.ForeignKeyField(Project, backref='_dataset_id_refs')
    dataset_id = pw.UUIDField()

class ProjectMember(pw.Model):
    '''Do not instantiate outside of `Project`.'''
    project_id = pw.ForeignKeyField(Project, backref='_member_id_refs')
    member_id = pw.CharField()