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
    # camel case for convenience in converting from SMRT Link representation
    id = pw.IntegerField(primary_key=True)
    name = pw.CharField()
    # state = pw.CharField()
    members = pw.CharField()
    # isActive = pw.BooleanField()
    # createdAt = pw.CharField()
    # updatedAt = pw.CharField()
    description = pw.CharField()

    def _get_updates(self, db_project):
        '''Identify changes between the instance and the database.'''
        updates = []
        for property in list(self._meta.fields):
            if getattr(self, property) != getattr(db_project, property):
                updates.append(property)
        if set(self._dataset_ids) != set(db_project._dataset_ids):
            updates.append('datasets')
        return updates

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
        if 'datasets' in kwargs: # external instance
            # initialize instance data
            self._datasets = kwargs.pop('datasets')
            self._dataset_ids = [dct['uuid'] for dct in self._datasets] # for comparison with database (internal) instance
            super().__init__(*args, **kwargs)
            # optionally, get updates using database
            db_project = Project.get_or_none(Project.id == self.id)
            if db_project:
                self.updates = self._get_updates(db_project)
            # update database with SMRT Link data. use insert query if project is new.
            project_is_new = False if db_project else True
            self.save(force_insert=project_is_new)
            for dct in self._datasets:
                (ProjectDataset.insert(project_id=self.id, dataset_id=dct['uuid'])
                               .on_conflict_ignore() # ignore error if this row already exists
                               .execute())
                (Dataset.insert(**dct)
                        .on_conflict_ignore() # ignore error if this row already exists
                        .execute())
        else: # internal instance
            super().__init__(*args, **kwargs) # populate instance with database data in kwargs
            assert hasattr(self, '_dataset_id_refs'), 'ProjectDataset foreign key backref not found'
            self._dataset_ids = [str(ref.dataset_id) for ref in self._dataset_id_refs]

    @property
    def datasets(self):
        return (Dataset
                .select()
                .join(ProjectDataset)
                .join(Project)
                .where(Project.id == self.id))

    def __str__(self):
        return str(self.name)

class Dataset(pw.Model):
    '''In SMRT Link, all fields use here are immutable.'''
    # camel case for convenience in converting from SMRT Link representation
    uuid = pw.UUIDField(primary_key=True)
    name = pw.CharField()
    path = pw.CharField()
    numChildren = pw.IntegerField()

    def __str__(self):
        return str(self.name)
    
    def __repr__(self) -> str:
        return self.uuid

class ProjectDataset(pw.Model):
    '''Do not instantiate outside of `Project`.'''
    project = pw.ForeignKeyField(Project, backref='_dataset_id_refs')
    dataset = pw.ForeignKeyField(Dataset)