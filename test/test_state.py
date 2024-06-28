import datetime

import app.state
import app

def test_last_job_update():
    assert app.state.LastJobUpdate.time() == '2000-01-01T00:00:00.000Z'
    time = '2016-12-19T16:12:47.014Z'
    app.state.LastJobUpdate.set(time)
    assert app.state.LastJobUpdate.time() == time

def test_permission_remove_expired_takes_effect():
    long_ago = '2000-01-01T00:00:00.000Z'
    app.state.Permission.insert(id='',
                                member_id='',
                                dataset_id='', 
                                expiry=long_ago).execute()
    assert app.state.Permission.select().count() == 1
    app.state.Permission.remove_expired()
    assert app.state.Permission.select().count() == 0

def test_permission_remove_expired_no_effect():
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    app.state.Permission.insert(id='',
                                member_id='',
                                dataset_id='', 
                                expiry=tomorrow).execute()
    assert app.state.Permission.select().count() == 1
    app.state.Permission.remove_expired()
    assert app.state.Permission.select().count() == 1

def test_dataset_update_project_id():
    dataset: app.state.Dataset = app.state.Dataset.create(uuid='1234',
                                                          project_id=1,
                                                          dir_path='whatever')
    assert dataset.project_id == 1
    dataset.update_project_id(2)
    assert dataset.project_id == 2