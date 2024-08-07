import globus_sdk
import datetime

import app.state

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
        app.logger.error(f'Error initializing Globus transfer client: {e}')

if app.GLOBUS_CLIENT_ID == '' or app.GLOBUS_CLIENT_SECRET == '':
    app.logger.error('No value given for Globus client ID and secret.')
    TRANSFER_CLIENT = None
else:
    TRANSFER_CLIENT = _get_transfer_client()

def _create_permission(dataset_uuid, dataset_dir, member_id: str) -> app.state.Permission:
    '''Raises Globus exception.'''
    expiry = datetime.datetime.now() + \
            datetime.timedelta(days=app.GLOBUS_PERMISSION_DAYS)
    rule_data = {
        "DATA_TYPE": "access",
        "principal_type": "identity",
        "principal": member_id,
        "path": dataset_dir,
        "permissions": "r",
        "expiration_date": expiry.isoformat()
    }
    permission_id = TRANSFER_CLIENT.add_endpoint_acl_rule(app.GLOBUS_COLLECTION_ID, rule_data)
    app.state.Permission.insert(id=permission_id,
                                member_id=member_id,
                                dataset_uuid=dataset_uuid,
                                expiry=expiry.isoformat()).execute()

def _delete_permission(access_rule_id):
    try:
        TRANSFER_CLIENT.delete_endpoint_acl_rule(app.GLOBUS_COLLECTION_ID, access_rule_id)
    except globus_sdk.TransferAPIError:
        ... # TODO Log the error

def remove_permissions(dataset_uuid, dataset_dir):
    permissions = app.state.Permission.get_by_dataset_id(dataset_uuid)
    for permission in permissions:
        remove_permission(dataset_uuid, dataset_dir, permission.member_id)

def remove_permission(dataset_uuid, dataset_dir, member_id: str):
    permission = app.state.Permission.get_by(member_id, dataset_uuid)
    if permission is None:
        app.logger.info(f'Permission for {member_id} to access {dataset_dir} not found.')
        return
    try:
        _delete_permission(permission.id)
    except globus_sdk.GlobusError as e:
        app.logger.error(f'Failed to remove permission for {member_id} to access {dataset_dir}: {e}')
        return
    permission.delete_instance()

def create_permission(dataset_uuid, dataset_dir, member_id: str):
    try:
        _create_permission(dataset_uuid, dataset_dir, member_id)
    except globus_sdk.GlobusAPIError as e:
        message = f'Failed to create Globus permission in collection ' + \
            f'{app.GLOBUS_COLLECTION_ID}: Globus API response message(s): ' \
            f'{e.message}, dataset.dir_path: {dataset_dir}, member_id: {member_id}'
        if e.code == 'Exists':
            app.logger.info(message)
        elif e.code == 'LimitExceeded':
            app.logger.error(f'ACTION REQUIRED: ' + message)
        else: # e.code == 'InvalidPath', etc.
            app.logger.error(message)