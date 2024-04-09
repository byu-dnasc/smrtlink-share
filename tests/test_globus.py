import app.globus as globus

IDENTITY_ID = "19ff6717-c44d-4ab4-983c-1eb2095beba4" # aknaupp@byu.edu

def test_add_acl_rule():
    # Define test data
    user_id = IDENTITY_ID
    project_path = "/"
    expected_rule_data = {
        "DATA_TYPE": "access",
        "principal_type": "identity",
        "principal": user_id,
        "path": project_path,
        "permissions": "r",
    }

    # Call the function
    rule_id = globus.add_acl_rule(user_id, project_path)
    
    globus.delete_acl_rule(rule_id)

# look up an access rule by id
def test_get_acl_rule():
    print(globus.get_acl_rules())

def test_access_rule_id_database():
    class FakeTransferClient:
        def add_endpoint_acl_rule(*args):
            return 'rule_id'

    globus.transfer_client = FakeTransferClient()

    globus.add_acl_rule('user_id', 'project_path', 'project_id')
    rule_ids = globus.get_project_access_rule_ids('project_id')
    assert rule_ids == ['rule_id']