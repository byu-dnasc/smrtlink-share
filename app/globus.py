import globus_sdk
import peewee as pw
from app import GLOBUS_CLIENT_ID, GLOBUS_CLIENT_SECRET, GLOBUS_COLLECTION_ID
from app.project import NewProject, UpdatedProject

ACL_CREATION_SCOPE='urn:globus:auth:scope:transfer.api.globus.org:all'

def _get_authorizer(scope):
    return globus_sdk.ClientCredentialsAuthorizer(
        globus_sdk.ConfidentialAppAuthClient(
            GLOBUS_CLIENT_ID,
            GLOBUS_CLIENT_SECRET
        ),
        scope
    )

def _get_transfer_client():
    try:
        authorizer = _get_authorizer(ACL_CREATION_SCOPE)
        return globus_sdk.TransferClient(authorizer=authorizer)
    except Exception as e:
        return None

class AccessRuleId(pw.Model):
    rule_id = pw.CharField(primary_key=True)
    project_id = pw.IntegerField()
    globus_user_id = pw.CharField()

TRANSFER_CLIENT = _get_transfer_client()

def _add_access_rule(user_id, project_path, project_id):
    rule_data = {
        "DATA_TYPE": "access",
        "principal_type": "identity",
        "principal": user_id,
        "path": project_path,
        "permissions": "r",
    }
    try:
        rule_id = TRANSFER_CLIENT.add_endpoint_acl_rule(GLOBUS_COLLECTION_ID, rule_data)
        AccessRuleId.create(
                rule_id=rule_id, 
                project_id=project_id, 
                globus_user_id=user_id
            )
    except globus_sdk.TransferAPIError as e:
        pass # TODO Log the error
    except pw.OperationalError as e:
        pass # TODO Log the error

def _get_access_rules():
    return TRANSFER_CLIENT.endpoint_acl_list(GLOBUS_COLLECTION_ID)

def _delete_access_rule(access_rule_id):
    try:
        TRANSFER_CLIENT.delete_endpoint_acl_rule(GLOBUS_COLLECTION_ID, access_rule_id)
    except globus_sdk.TransferAPIError:
        pass # TODO Log the error

def _delete_member(user_id, project_id):
    rule_id = (AccessRuleId.select(AccessRuleId.rule_id)
                            .where(AccessRuleId.project_id == project_id,
                                   AccessRuleId.globus_user_id == user_id)
                            .execute())
    _delete_access_rule(rule_id)
    AccessRuleId.delete().where(AccessRuleId.rule_id == rule_id).execute()

def _get_project_access_rule_ids(project_id):
    ids = AccessRuleId.select().where(AccessRuleId.project_id == project_id)
    return [id.rule_id for id in ids]

def new(project: NewProject):
    for member in project.members:
        _add_access_rule(member, project.dir_name, project.id)

def update(project: UpdatedProject):
    for member in project.new_members:
        _add_access_rule(member, project.dir_name, project.id)
    for member in project.members_to_remove:
        _delete_member(member, project.id)

def delete(project_id):
    rule_ids = _get_project_access_rule_ids(project_id)
    for rule_id in rule_ids:
        _delete_access_rule(rule_id)