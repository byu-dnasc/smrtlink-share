from app.state import LastJobUpdate

def test_last_job_update():
    assert LastJobUpdate.time() == '2000-01-01T00:00:00.000Z'
    time = '2016-12-19T16:12:47.014Z'
    LastJobUpdate.set(time)
    assert LastJobUpdate.time() == time