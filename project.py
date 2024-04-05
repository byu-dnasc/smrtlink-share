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
        Both types of instances have a variable for each of the `peewee` 
        'fields'. These are initialized by `super().__init__()`. Both types of 
        instances also have a list of dataset ids, initialized by this method.
        The 'internal' type of instance has only the variables mentioned above
        and should only be used within `Project`.
        The 'external' type of instance has one more optional variable called
        `updates`, which is a list of field names that have changed since the 
        last time the app checked SMRT Link for updates. If the project is new
        (i.e., it does not exist in the database), then `updates` is omitted.

        Another key difference between the two types of instances is that the
        internal instance is populated with data from the database, while the
        external instance is populated with data from SMRT Link.

        :param kwargs: when using init directly (as in `smrtlink._dict_to_project`),
        `kwargs` is a dictionary of project data from SMRT Link, as well as a list 
        of dataset ids under the key 'dataset_ids'.
        '''
        if 'dataset_ids' in kwargs: # external instance
            # initialize instance data
            self.dataset_ids = kwargs.pop('dataset_ids')
            super().__init__(*args, **kwargs) # pass SMRT Link data to super
            # optionally, get updates using database
            db_project = Project.get_or_none(Project.id == self.id)
            if db_project:
                self.updates = self._get_updates(db_project)
            # update database with SMRT Link data
            self.save(force_insert=True)
            DatasetId.bulk_create([DatasetId(id=uuid, project=self) for uuid in self.dataset_ids])
        else: # internal instance
            super().__init__(*args, **kwargs) # populate instance with database data in kwargs
                                              # and generate self._datasets from backref
            assert hasattr(self, '_datasets'), 'Dataset foreign key backref not found'
            self.dataset_ids = [str(ds.id) for ds in self._datasets]
    
    def __str__(self):
        return str(self.name)

class DatasetId(pw.Model):
    '''Do not instantiate outside of `Project`.'''
    id = pw.UUIDField(primary_key=True)
    project = pw.ForeignKeyField(Project, backref='_datasets')

def init_db(db_file):
    db = pw.SqliteDatabase(db_file)
    Project.bind(db)
    DatasetId.bind(db)
    with db:
        db.create_tables([Project, DatasetId], safe=True)
    return db