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

def _create_permission(dataset: app.BaseDataset, member_id: str) -> app.state.Permission:
    '''Raises Globus exception.'''
    rule_data = {
        "DATA_TYPE": "access",
        "principal_type": "identity",
        "principal": member_id,
        "path": dataset.dir_path,
        "permissions": "r",
    }
    permission_id = TRANSFER_CLIENT.add_endpoint_acl_rule(app.GLOBUS_COLLECTION_ID, rule_data)
    app.state.Permission.add(id=permission_id,
                                dataset_id=dataset.uuid,
                                member_id=member_id)

def _delete_permission(access_rule_id):
    try:
        TRANSFER_CLIENT.delete_endpoint_acl_rule(app.GLOBUS_COLLECTION_ID, access_rule_id)
    except globus_sdk.TransferAPIError:
        ... # TODO Log the error

def remove_permissions(dataset: app.BaseDataset):
    permissions = app.state.Permission.where_dataset_id(dataset.uuid)
    for permission in permissions:
        remove_permission(dataset, permission.member_id)

def remove_permission(dataset: app.BaseDataset, member_id: str):
    permission = app.state.Permission.where(member_id, dataset.uuid)
    if permission is None:
        app.logger.info(f'Permission for {member_id} to access {dataset.dir_path} not found.')
        return
    try:
        _delete_permission(permission.id)
    except globus_sdk.GlobusError as e:
        app.logger.error(f'Failed to remove permission for {member_id} to access {dataset.dir_path}: {e}')
        return
    permission.delete_instance()

def create_permission(dataset: app.BaseDataset, member_id: str):
    try:
        _create_permission(dataset, member_id)
    except globus_sdk.GlobusAPIError as e:
        message = f'Failed to create Globus permission in collection ' + \
            f'{app.GLOBUS_COLLECTION_ID}: Globus API response message(s): ' \
            f'{e.message}, dataset.dir_path: {dataset.dir_path}, member_id: {member_id}'
        if e.code == 'Exists':
            app.logger.info(message)
        elif e.code == 'LimitExceeded':
            app.logger.error(f'ACTION REQUIRED: ' + message)
        else: # e.code == 'InvalidPath', etc.
            app.logger.error(message)