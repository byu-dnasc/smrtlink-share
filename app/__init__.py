import os

class EnvVarNotFoundError(Exception):
    pass

class OutOfSyncError(Exception):
    pass

def get_env_var(var):
    if var not in os.environ:
        raise EnvVarNotFoundError(f'{var} not found in environment variables')
    return os.environ[var]
