import app.state
import app

def test_last_job_update():
    assert app.state.LastJobUpdate.time() == '2000-01-01T00:00:00.000Z'
    time = '2016-12-19T16:12:47.014Z'
    app.state.LastJobUpdate.set(time)
    assert app.state.LastJobUpdate.time() == time

def test_permission():
    app.state.Permission.add('id', 'member_id', 'dataset_id')
    app.state.Permission.get_by('member_id', 'dataset_id')