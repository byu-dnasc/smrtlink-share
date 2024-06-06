import grp
import pwd
import os

from app import STAGING_ROOT, APP_USER, GROUP_NAME, APP_PORT
import app.smrtlink as smrtlink
import app.globus as globus

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

# check that the app is running as the correct group
try:
    gid = grp.getgrnam(GROUP_NAME).gr_gid
except KeyError:
    print(f"Group '{GROUP_NAME}' not found")
    exit(1)
if gid != os.getgid():
    print(f"App must be run as group '{GROUP_NAME}'")
    exit(1)

# initialize and run the app
from app.server import App

app = App(('localhost', APP_PORT))

app.run()