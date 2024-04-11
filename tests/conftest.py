import pytest
import os
import peewee as pw
from app.project import Project, ProjectDataset, Dataset

# Configure environment variables
import dotenv
dotenv.load_dotenv()
os.environ['GLOBUS_COLLECTION_ID'] = 'test_collection_id'

# import modules that rely on environment variables
import app.smrtlink as smrtlink
from app.globus import AccessRuleId

@pytest.fixture(autouse=True)
def init_db():
    db = pw.SqliteDatabase(':memory:')
    Project.bind(db)
    ProjectDataset.bind(db)
    Dataset.bind(db)
    AccessRuleId.bind(db)
    db.create_tables([Project, ProjectDataset, Dataset, AccessRuleId], safe=True)
    yield
    db.close()

