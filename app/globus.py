import globus_sdk
import peewee as pw
from app.server import get_env_var

CLIENT_ID = get_env_var('GLOBUS_CLIENT_ID')
CLIENT_SECRET = get_env_var('GLOBUS_CLIENT_SECRET')
COLLECTION_ID = get_env_var('GLOBUS_COLLECTION_ID')
ACL_CREATION_SCOPE='urn:globus:auth:scope:transfer.api.globus.org:all'

def get_authorizer(scope):
    return globus_sdk.ClientCredentialsAuthorizer(
        globus_sdk.ConfidentialAppAuthClient(
            CLIENT_ID,
            CLIENT_SECRET
        ),
        scope
    )

def _get_transfer_client():
    try:
        authorizer = get_authorizer(ACL_CREATION_SCOPE)
        return globus_sdk.TransferClient(authorizer=authorizer)
    except Exception as e:
        return None

TRANSFER_CLIENT = _get_transfer_client()

def add_acl_rule(user_id, project_path, project_id):
    rule_data = {
        "DATA_TYPE": "access",
        "principal_type": "identity",
        "principal": user_id,
        "path": project_path,
        "permissions": "r",
    }
    try:
        rule_id = TRANSFER_CLIENT.add_endpoint_acl_rule(COLLECTION_ID, rule_data)
        AccessRuleId.create(rule_id=rule_id, project_id=project_id)
    except globus_sdk.TransferAPIError as e:
        pass # TODO Log the error
    except pw.OperationalError as e:
        pass # TODO Log the error

def get_acl_rules():
    return TRANSFER_CLIENT.endpoint_acl_list(COLLECTION_ID)

def delete_acl_rule(access_rule_id):
    '''
    Use case 1: receive request to delete a project (get rule id from database)
    Use case 2: access rule is too old (get rule id directly from Globus)
    '''
    try:
        TRANSFER_CLIENT.delete_endpoint_acl_rule(COLLECTION_ID, access_rule_id)
    except globus_sdk.TransferAPIError:
        pass # TODO Log the error

class AccessRuleId(pw.Model):
    rule_id = pw.CharField(primary_key=True)
    project_id = pw.IntegerField()

def get_project_access_rule_ids(project_id):
    ids = AccessRuleId.select().where(AccessRuleId.project_id == project_id)
    return [id.rule_id for id in ids]