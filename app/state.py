import peewee as pw
from app import db

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
