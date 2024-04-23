import app.globus as globus

ADMIN_ID = "19ff6717-c44d-4ab4-983c-1eb2095beba4" # aknaupp@byu.edu
NON_ADMIN_ID = "65af3497-1ad5-4a79-8c5b-cec928605c1c" # adkna@byu.edu
DNASC_ID = "45a581b4-78bc-4475-83b0-55849ea0ca11" # dnasc@globusid.org

def test_add_access_rule_live():
    user_id = NON_ADMIN_ID
    project_path = "/"
    rule_id = globus.add_access_rule(user_id, project_path, 'project_id')
    print(rule_id)