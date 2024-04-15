import app.globus as globus

IDENTITY_ID = "19ff6717-c44d-4ab4-983c-1eb2095beba4" # aknaupp@byu.edu

def test_add_access_rule():
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
    rule_id = globus.add_access_rule(user_id, project_path)

# look up an access rule by id
def test_get_acl_rule():
    print(globus.get_access_rules())

def test_access_rule_id_database():
    class FakeTransferClient:
        def add_endpoint_acl_rule(*args):
            return 'rule_id'

    globus.TRANSFER_CLIENT = FakeTransferClient()

    globus.add_access_rule('user_id', 'project_path', 'project_id')
    rule_ids = globus.get_project_access_rule_ids('project_id')
    assert rule_ids == ['rule_id']

def test_get_project_access():
    globus.AccessRuleId.create(
            rule_id='rule_id', 
            project_id='project_id', 
            globus_user_id='user_id'
        )
    rule_ids = globus.get_project_access_rule_ids('project_id')
    assert rule_ids == ['rule_id']

def test_get_access_rule_id():
    globus.AccessRuleId.create(
            rule_id='rule_id', 
            project_id='project_id', 
            globus_user_id='user_id'
        )
    rule_id = globus._get_access_rule_id('user_id', 'project_id')
    assert rule_id == ['rule_id']