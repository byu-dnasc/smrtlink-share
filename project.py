import peewee as pw

db = pw.SqliteDatabase('project.db')

class Project(pw.Model):
    id = pw.IntegerField(primary_key=True)
    name = pw.CharField()
    state = pw.CharField()
    members = pw.CharField()
    datasets = pw.CharField()
    is_active = pw.BooleanField()
    created_at = pw.CharField()
    updated_at = pw.CharField()
    description = pw.CharField()

    class Meta:
        database = db
