import globus_sdk
import os
import peewee as pw

def get_env_var(var):
    if var not in os.environ:
        raise KeyError(f'{var} not found in environment variables')
    return os.environ[var]

CLIENT_ID = get_env_var('GLOBUS_CLIENT_ID')
CLIENT_SECRET = get_env_var('GLOBUS_CLIENT_SECRET')
COLLECTION_ID = get_env_var('GLOBUS_COLLECTION_ID')
ACL_CREATION_SCOPE='urn:globus:auth:scope:transfer.api.globus.org:all'
visible_to_identities = [CLIENT_ID]
VISIBLE_TO_URNS = [f'urn:globus:auth:identity:{i}' for i in visible_to_identities]

def get_authorizer(scope):
    return globus_sdk.ClientCredentialsAuthorizer(
        globus_sdk.ConfidentialAppAuthClient(
            CLIENT_ID,
            CLIENT_SECRET
        ),
        scope
    )

def get_transfer_client():
    try:
        authorizer = get_authorizer(ACL_CREATION_SCOPE)
        return globus_sdk.TransferClient(authorizer=authorizer)
    except globus_sdk.AuthAPIError as e:
        print('Failed to get TransferClient: ' + str(e))
        return None

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
        rule_id = transfer_client.add_endpoint_acl_rule(COLLECTION_ID, rule_data)
        AccessRuleId.create(rule_id=rule_id, project_id=project_id)
    except globus_sdk.TransferAPIError as e:
        pass # TODO Log the error
    except pw.OperationalError as e:
        pass # TODO Log the error

def get_acl_rules():
    return transfer_client.endpoint_acl_list(COLLECTION_ID)

def delete_acl_rule(access_rule_id):
    '''
    Use case 1: receive request to delete a project (get rule id from database)
    Use case 2: access rule is too old (get rule id directly from Globus)
    '''
    try:
        transfer_client.delete_endpoint_acl_rule(COLLECTION_ID, access_rule_id)
    except globus_sdk.TransferAPIError:
        pass # TODO Log the error

class AccessRuleId(pw.Model):
    rule_id = pw.CharField(primary_key=True)
    project_id = pw.IntegerField()

def get_project_access_rule_ids(project_id):
    ids = AccessRuleId.select().where(AccessRuleId.project_id == project_id)
    return [id.rule_id for id in ids]