import os
import logging
import dotenv

if not os.path.exists('.env'):
    raise ImportError('.env file not found.')
dotenv.load_dotenv()

try:
    GLOBUS_CLIENT_ID = os.environ.get('GLOBUS_CLIENT_ID')
    GLOBUS_CLIENT_SECRET = os.environ.get('GLOBUS_CLIENT_SECRET')
    GLOBUS_COLLECTION_ID = os.environ.get('GLOBUS_COLLECTION_ID')
    SMRTLINK_HOST = os.environ.get('SMRTLINK_HOST')
    SMRTLINK_PORT = os.environ.get('SMRTLINK_PORT')
    SMRTLINK_USER = os.environ.get('SMRTLINK_USER')
    SMRTLINK_PASS = os.environ.get('SMRTLINK_PASS')
    DB_PATH = os.environ.get('DB_PATH')
    GROUP_NAME = os.environ.get('GROUP_NAME')
    APP_USER = os.environ.get('APP_USER')
    GLOBUS_PERMISSION_DAYS = os.environ.get('GLOBUS_PERMISSION_DAYS')
    STAGING_ROOT = os.environ.get('STAGING_ROOT')
except KeyError as e:
    raise ImportError(f"Variable {e} not found in .env file.")

class OutOfSyncError(Exception):
    def __init__(self, message, project) -> None:
        super().__init__(message)
        self.project = project
        self.message = message
    
    def __str__(self) -> str:
        return f'{self.message}'

logger = logging.getLogger('smrtlink-share')
logger.setLevel(logging.INFO)
log_formatter = logging.Formatter(
    '%(levelname)s: at %(asctime)s, %(funcName)s (%(filename)s) said "%(message)s"', datefmt='%H:%M:%S'
)
logger.addHandler(
    (logging.FileHandler('smrtlink-share.log')
            .setFormatter(log_formatter))
)