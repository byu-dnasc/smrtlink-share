import globus

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