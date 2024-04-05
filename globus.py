import globus_sdk
import json
import os
import peewee as pw

CREDENTIALS_FILE_PATH = f'/home/{os.environ["USER"]}/smrtlink-share/credentials.json' 
APP_CLIENT_UUID = '762432c3-3ff0-43cc-af07-1ccda52be14b'
visible_to_identities = [APP_CLIENT_UUID]
VISIBLE_TO_URNS = [f'urn:globus:auth:identity:{i}' for i in visible_to_identities]

def _valid_credentials_file_accessible():
    if os.path.isfile(CREDENTIALS_FILE_PATH):
        with open(CREDENTIALS_FILE_PATH) as f:
            j = json.load(f)
            if 'Globus Client ID' in j and \
               'Globus Client Secret' in j:
                return True
            else:
                raise KeyError(f'{CREDENTIALS_FILE_PATH} missing property.')
    else:
        raise Exception(f'{CREDENTIALS_FILE_PATH} does not exist.')

def _read_id_secret():
    try:
        _valid_credentials_file_accessible()
    except Exception as e:
        print('Failed to get Globus client credentials: ' + str(e))
    with open(CREDENTIALS_FILE_PATH) as f:
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
    try:
        authorizer = get_authorizer(ACL_CREATION_SCOPE)
        globus_sdk.TransferClient(authorizer=authorizer)
    except globus_sdk.AuthAPIError as e:
        print('Failed to get TransferClient: ' + str(e))

transfer_client = get_transfer_client()

def add_acl_rule(user_id, project_path, project_id):
    rule_data = {
        "DATA_TYPE": "access",
        "principal_type": "identity",
        "principal": user_id,
        "path": project_path,
        "permissions": "r",
    }
    try:
        rule_id = transfer_client.add_endpoint_acl_rule(GUEST_COLLECTION_ID, rule_data)
        AccessRuleId.create(rule_id=rule_id, project_id=project_id)
    except globus_sdk.TransferAPIError as e:
        pass # TODO Log the error
    except pw.OperationalError as e:
        pass # TODO Log the error

def get_acl_rules():
    return transfer_client.endpoint_acl_list(GUEST_COLLECTION_ID)

def delete_acl_rule(access_rule_id):
    '''
    Use case 1: receive request to delete a project (get rule id from database)
    Use case 2: access rule is too old (get rule id directly from Globus)
    '''
    try:
        transfer_client.delete_endpoint_acl_rule(GUEST_COLLECTION_ID, access_rule_id)
    except globus_sdk.TransferAPIError:
        pass # TODO Log the error

class AccessRuleId(pw.Model):
    rule_id = pw.CharField(primary_key=True)
    project_id = pw.IntegerField()

def get_project_access_rule_ids(project_id):
    ids = AccessRuleId.select().where(AccessRuleId.project_id == project_id)
    return [id.rule_id for id in ids]