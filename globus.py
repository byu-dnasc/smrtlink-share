import globus_sdk
import json
import os

class Constants:
    CREDENTIALS_FILE_PATH = f'/home/{os.environ["USER"]}/smrtlink-share/credentials.json' 
    APP_CLIENT_UUID = '762432c3-3ff0-43cc-af07-1ccda52be14b'
    visible_to_identities = [APP_CLIENT_UUID]
    VISIBLE_TO_URNS = [f'urn:globus:auth:identity:{i}' for i in visible_to_identities]

def _valid_credentials_file_accessible():
    if os.path.isfile(Constants.CREDENTIALS_FILE_PATH):
        with open(Constants.CREDENTIALS_FILE_PATH) as f:
            j = json.load(f)
            if 'Globus Client ID' in j and \
               'Globus Client Secret' in j:
                return True
            else:
                raise KeyError(f'{Constants.CREDENTIALS_FILE_PATH} missing property.')
    else:
        raise Exception(f'{Constants.CREDENTIALS_FILE_PATH} does not exist.')

def _read_id_secret():
    try:
        _valid_credentials_file_accessible()
    except Exception as e:
        print('Failed to get Globus client credentials: ' + str(e))
    with open(Constants.CREDENTIALS_FILE_PATH) as f:
        j = json.load(f)
        return j['Globus Client ID'], j['Globus Client Secret']

def get_authorizer(scope):
    client_id, client_secret = _read_id_secret()
    return globus_sdk.ClientCredentialsAuthorizer(
        globus_sdk.ConfidentialAppAuthClient(
            client_id,
            client_secret
        ),
        scope
    )

GUEST_COLLECTION_ID = "b550603b-7baa-43fa-b380-939d15549345" # DNASC
IDENTITY_ID = "19ff6717-c44d-4ab4-983c-1eb2095beba4" # aknaupp@byu.edu
ACL_CREATION_SCOPE='urn:globus:auth:scope:transfer.api.globus.org:all'

def get_transfer_client():
    authorizer = get_authorizer(ACL_CREATION_SCOPE)
    return globus_sdk.TransferClient(authorizer=authorizer)

def add_acl_rule(transfer_client, rule_data):
    rule_data = {
        "DATA_TYPE": "access",
        "principal_type": "identity",
        "principal": IDENTITY_ID,
        "path": "/ABHelix EXP23000689 CCS/",
        "permissions": "r",
    }
    return transfer_client.add_endpoint_acl_rule(GUEST_COLLECTION_ID, rule_data)

def get_acl_rules(transfer_client):
    return transfer_client.endpoint_acl_list(GUEST_COLLECTION_ID)