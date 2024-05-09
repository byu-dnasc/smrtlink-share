import pytest
import peewee as pw

# Configure environment variables
import dotenv
dotenv.load_dotenv()

from app.project import ProjectModel, ProjectDataset, ProjectMember
import app

# import modules that rely on environment variables
import app.smrtlink as smrtlink
from app.globus import AccessRuleId

@pytest.fixture(autouse=True)
def init_db():
    app.db = pw.SqliteDatabase(':memory:')
    ProjectModel.bind(app.db)
    ProjectDataset.bind(app.db)
    ProjectMember.bind(app.db)
    app.db.create_tables([ProjectModel,
                          ProjectDataset, 
                          ProjectMember], 
                          safe=True)
    yield
    app.db.close()

