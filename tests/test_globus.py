import app.globus as globus
import uuid

IDENTITY_ID = "19ff6717-c44d-4ab4-983c-1eb2095beba4" # aknaupp@byu.edu

class FakeTransferClient:
    def add_endpoint_acl_rule(*args):
        return uuid.uuid4()
    def delete_endpoint_acl_rule(*args):
        pass
globus.TRANSFER_CLIENT = FakeTransferClient()

def test_add_access_rule_live():
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
    rule_id = globus.add_access_rule(user_id, project_path, 'project_id')

# look up an access rule by id on a live globus collection
def test_get_acl_rule_live():
    print(globus.get_access_rules())

def test_get_project_access_rule_ids():
    globus.AccessRuleId.create(
            rule_id='rule_id', 
            project_id='project_id', 
            globus_user_id='user_id'
        )
    rule_ids = globus.get_project_access_rule_ids('project_id')
    assert len(rule_ids) == 1

def test_add_access_rule():
    user_id = "asdf"
    project_path = "/"
    project_id = 1
    globus.add_access_rule(user_id, project_path, project_id)
    project_rule_ids = globus.get_project_access_rule_ids(project_id)
    assert len(project_rule_ids) == 1

def test_delete_access_rule():
    user_id = "asdf"
    project_path = "/"
    project_id = 1
    globus.add_access_rule(user_id, project_path, project_id)
    globus.delete_access_rule(user_id, project_id)
    project_rule_ids = globus.get_project_access_rule_ids(project_id)
    assert len(project_rule_ids) == 0