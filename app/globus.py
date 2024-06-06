import globus_sdk

import app.state
import app

ACL_CREATION_SCOPE='urn:globus:auth:scope:transfer.api.globus.org:all'

def _get_authorizer(scope):
    return globus_sdk.ClientCredentialsAuthorizer(
        globus_sdk.ConfidentialAppAuthClient(
            app.GLOBUS_CLIENT_ID,
            app.GLOBUS_CLIENT_SECRET
        ),
        scope
    )

def _get_transfer_client():
    try:
        authorizer = _get_authorizer(ACL_CREATION_SCOPE)
        return globus_sdk.TransferClient(authorizer=authorizer)
    except Exception as e:
        return None

TRANSFER_CLIENT = _get_transfer_client()

def _add_permission(user_id, path) -> str:
    rule_data = {
        "DATA_TYPE": "access",
        "principal_type": "identity",
        "principal": user_id,
        "path": path,
        "permissions": "r",
    }
    try:
        return TRANSFER_CLIENT.add_endpoint_acl_rule(app.GLOBUS_COLLECTION_ID, rule_data)
    except globus_sdk.TransferAPIError as e:
        ... # TODO Log the error
        return None

def _get_access_rules():
    return TRANSFER_CLIENT.endpoint_acl_list(app.GLOBUS_COLLECTION_ID)

def _delete_permission(access_rule_id):
    try:
        TRANSFER_CLIENT.delete_endpoint_acl_rule(app.GLOBUS_COLLECTION_ID, access_rule_id)
    except globus_sdk.TransferAPIError:
        ... # TODO Log the error

def remove_permissions(dataset_id):
    permissions = (app.state.Permission.select()
                                        .where(app.state.Permission.dataset_id == dataset_id)
                                        .execute())
    for permission in permissions:
        _delete_permission(permission.id)
        permission.delete_instance()

def remove_permission(dataset_id, member_id):
    permission = (app.state.Permission.get(app.state.Permission.dataset_id == dataset_id,
                                           app.state.Permission.member_id == member_id))
    _delete_permission(permission.id)
    permission.delete_instance()

def create_permission(dataset, member_id):
    permission_id = _add_permission(member_id, dataset.dir_path)
    app.state.Permission.insert(id=permission_id,
                                member_id=member_id,
                                dataset_id=dataset.id).execute()