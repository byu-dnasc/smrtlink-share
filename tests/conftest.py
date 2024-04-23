import pytest
import peewee as pw

# Configure environment variables
import dotenv
dotenv.load_dotenv()

from app.project import Project, ProjectDataset, ProjectMember
from app.staging import DatasetDirectory

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
    DatasetDirectory.bind(db)
    db.create_tables([Project, ProjectDataset, ProjectMember, AccessRuleId, DatasetDirectory], safe=True)
    yield
    db.close()

