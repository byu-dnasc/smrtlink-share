import os
import logging

class EnvVarNotFoundError(Exception):
    pass

class OutOfSyncError(Exception):
    pass

def get_env_var(var):
    if var not in os.environ:
        raise EnvVarNotFoundError(f'{var} not found in environment variables')
    return os.environ[var]

logger = logging.getLogger('smrtlink-share')
logger.setLevel(logging.INFO)
log_formatter = logging.Formatter(
    'At %(asctime)s, %(funcName)s (%(filename)s) said "%(message)s"', datefmt='%H:%M:%S'
)
logger.addHandler(
    (logging.FileHandler('smrtlink-share.log')
            .setFormatter(log_formatter))
)