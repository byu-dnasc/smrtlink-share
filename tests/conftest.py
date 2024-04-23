import pytest
import peewee as pw
from app.project import Project, ProjectDataset, ProjectMember

# Configure environment variables
import dotenv
dotenv.load_dotenv()

# import modules that rely on environment variables
import app.smrtlink as smrtlink
from app.globus import AccessRuleId

@pytest.fixture(autouse=True)
def init_db():
    db = pw.SqliteDatabase(':memory:')
    Project.bind(db)
    ProjectDataset.bind(db)
    ProjectMember.bind(db)
    AccessRuleId.bind(db)
    db.create_tables([Project, ProjectDataset, ProjectMember, AccessRuleId], safe=True)
    yield
    db.close()

