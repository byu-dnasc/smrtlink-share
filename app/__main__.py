import logging
import os
import grp
import dotenv
import peewee as pw

from app.project import Project
from app import get_env_var, EnvVarNotFoundError

# report and exit if any environment variables are missing
dotenv.load_dotenv()
try:
    import app.smrtlink as smrtlink
    from app.globus import AccessRuleId
    get_env_var('GROUP_NAME')
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
try:
    db = pw.SqliteDatabase(os.environ['DB_PATH'])
except Exception as e:
    print(f"Failed to initialize database: {e}")
    exit(1)
Project.bind(db)
AccessRuleId.bind(db)
db.create_tables([Project, AccessRuleId], safe=True)

# check that the app is running as the correct group
group_name = get_env_var('GROUP_NAME')
try:
    gid = grp.getgrnam(group_name).gr_gid
except KeyError:
    print(f"Group '{group_name}' not found")
    exit(1)
if gid != os.getgid():
    print(f"App must be run as group '{group_name}'")
    exit(1)

# set umask to 0 to give full permissions to group
os.umask(0)

# initialize and run the app
from app.server import App

logging.basicConfig(filename='request.log', level=logging.INFO)

app = App(('localhost', 9093), logging.getLogger(__name__))

app.run()