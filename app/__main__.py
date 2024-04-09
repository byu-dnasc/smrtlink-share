import logging
import os
import peewee as pw
import dotenv
dotenv.load_dotenv()

# report and exit if any environment variables are missing
from app import EnvVarNotFoundError
try:
    import app.smrtlink as smrtlink
    import app.globus as globus
except EnvVarNotFoundError as e:
    print(e)
    exit(1)

# report and exit if any web clients failed to initialize
if smrtlink.CLIENT is None:
    print('SMRT Link client failed to initialize')
    exit(1)
if globus.TRANSFER_CLIENT is None:
    print('Globus transfer client failed to initialize')
    exit(1)

# initialize and bind database to models
from app.project import Project, DatasetId
from app.globus import AccessRuleId

try:
    db = pw.SqliteDatabase(os.environ['DB_PATH'])
except Exception as e:
    print(f"Failed to initialize database: {e}")
    exit(1)
Project.bind(db)
DatasetId.bind(db)
AccessRuleId.bind(db)
db.create_tables([Project, DatasetId, AccessRuleId], safe=True)

# initialize and run the app
from app.server import App

logging.basicConfig(filename='request.log', level=logging.INFO)

app = App(('localhost', 9093), logging.getLogger(__name__))

app.run()