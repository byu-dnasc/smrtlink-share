import logging
import os
import grp
import pwd
import peewee as pw

from app.project import Project, ProjectDataset, ProjectMember
from app import STAGING_ROOT, APP_USER, GROUP_NAME
import app.smrtlink as smrtlink
import app.globus as globus
import app.staging as staging

# check that all modules have initialized properly
if smrtlink.CLIENT is None:
    print('SMRT Link client failed to initialize')
    exit(1)
if globus.TRANSFER_CLIENT is None:
    print('Globus transfer client failed to initialize')
    exit(1)
if not os.path.exists(STAGING_ROOT):
    print(f"Staging root directory '{STAGING_ROOT}' specified in .env file does not exist")
    exit(1)
if not os.path.isdir(STAGING_ROOT):
    print(f"Staging root directory '{STAGING_ROOT}' specified in .env file is not a directory")
    exit(1)
dir_owner = pwd.getpwuid(os.stat(STAGING_ROOT).st_uid).pw_name
if dir_owner != APP_USER:
    print(f"Staging root directory '{STAGING_ROOT}' is not owned by '{APP_USER}'")
    exit(1)

# initialize and bind database to models
try:
    db = pw.SqliteDatabase(os.environ['DB_PATH'])
except Exception as e:
    print(f"Failed to initialize database: {e}")
    exit(1)
Project.bind(db)
ProjectDataset.bind(db)
ProjectMember.bind(db)
staging.DatasetDirectory.bind(db)
globus.AccessRuleId.bind(db)
db.create_tables([
    Project, 
    ProjectDataset, 
    ProjectMember, 
    globus.AccessRuleId, 
    staging.DatasetDirectory],
    safe=True)

# check that the app is running as the correct group
try:
    gid = grp.getgrnam(GROUP_NAME).gr_gid
except KeyError:
    print(f"Group '{GROUP_NAME}' not found")
    exit(1)
if gid != os.getgid():
    print(f"App must be run as group '{GROUP_NAME}'")
    exit(1)

# set umask to 0 to give full permissions to group
os.umask(0)

# initialize and run the app
from app.server import App

app = App(('localhost', 9093))

app.run()