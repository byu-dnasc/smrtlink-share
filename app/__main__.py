import getpass
import grp
import os

def abort(message):
    print(f"Aborting app: {message}")
    exit(1)

import app

# check that the app is running as the correct user and group
if app.APP_USER != getpass.getuser():
    abort(f"App must be run as user '{app.APP_USER}' specified in .env file.")
try:
    gid = grp.getgrnam(app.GROUP_NAME).gr_gid
except KeyError:
    abort(f"Group '{app.GROUP_NAME}' not found")
if gid != os.getgid():
    abort(f"App must be run as group '{app.GROUP_NAME}'")

# check that all modules initialize properly
import app.smrtlink
import app.globus
import app.filesystem # import to create staging root directory
if app.smrtlink.CLIENT is None:
    abort('SMRT Link client failed to initialize (check log for error message).')
if app.globus.TRANSFER_CLIENT is None:
    abort('Globus transfer client failed to initialize (check log for error message).')
if not os.path.exists(app.STAGING_ROOT): # otherwise, directory exists and we assume it has proper permissions as set in app/filesystem.py
    abort(f"Staging root directory '{app.STAGING_ROOT}' specified in .env file does not exist.")

# initialize and run the app
from app.server import App

app = App(('localhost', app.APP_PORT))

app.run()