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
    state = pw.CharField()
    members = pw.CharField()
    isActive = pw.BooleanField()
    createdAt = pw.CharField()
    updatedAt = pw.CharField()
    description = pw.CharField()

    def _get_updates(self, db_project):
        '''Identify changes between the instance and the database.'''
        properties = self._meta.fields + ['dataset_ids']
        updates = []
        for property in properties:
            if getattr(self, property) != getattr(db_project, property):
                updates.append(property)
        return updates

    def __init__(self, *args, **kwargs):
        '''
        There are two types of `Project` instances, internal and external,
        whose initialization is handled respectively by one or the other
        of the two branches of this method.
        Both types of instances have an attribute for each of the `peewee` 
        'fields'. These are initialized by `super().__init__()`. Both types of 
        instances also have a list of dataset ids, initialized by this method.
        The 'internal' type of instance has only the attributes mentioned above
        and should only be used within the class.
        The 'external' type of instance has at least one more attribute called
        `is_new`, which is true if the instance is not found in the database. 
        If `is_new` is False, then the instance will also have `updates`,
        which is a list of field names that have changed since the last time 
        the app checked SMRT Link for updates.

        :param kwargs: when using init directly (as in `smrtlink._dict_to_project`),
        kwargs is a dictionary of project data from SMRT Link which includes a
        list of dataset ids under the key 'datasets'.
        '''
        if 'datasets' in kwargs: # external instance
            self.dataset_ids = kwargs.pop('datasets')
            super().__init__(*args, **kwargs) # populate instance with SMRT Link data
            db_project = Project.get_or_none(Project.id == self.id)
            if db_project:
                self.is_new = False
                self.updates = self._get_updates(db_project)
            else:
                self.is_new = True
        else: # internal instance
            super().__init__(*args, **kwargs) # populate instance with database data 
                                              # and generate self._datasets from backref
            assert hasattr(self, '_datasets'), 'Dataset foreign key backref not found'
            self.dataset_ids = [str(ds.id) for ds in self._datasets]
    
    def update_db(self):
        '''Update the database with the project's data.'''
        self.save(force_insert=True) # override query type UPDATE with INSERT
        Dataset.bulk_create([Dataset(id=uuid, project=self) for uuid in self.dataset_ids])
    
    def __str__(self):
        return str(self.name)

class Dataset(pw.Model):
    '''Do not instantiate outside of `Project`.'''
    id = pw.UUIDField(primary_key=True)
    project = pw.ForeignKeyField(Project, backref='_datasets')

def init_db(db_file):
    db = pw.SqliteDatabase(db_file)
    Project.bind(db)
    Dataset.bind(db)
    with db:
        db.create_tables([Project, Dataset], safe=True)
    return db