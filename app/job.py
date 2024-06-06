import time
import concurrent.futures

import app.collection
import app.smrtlink
import app.state
import app

FAIL_STATES = {'FAILED', 'TERMINATED', 'ABORTED'}
PENDING_STATES = {'CREATED', 'SUBMITTED', 'RUNNING'}
SUCCESSFUL = 'SUCCESSFUL'

def get_analyses(dataset):
    completed = []
    pending = []
    jobs = app.smrtlink.get_dataset_jobs(dataset.id)
    for job in jobs:
        if job['state'] in FAIL_STATES:
            continue
        if job['state'] is SUCCESSFUL:
            files = app.smrtlink.get_job_files(job['id'])
            completed.append(app.collection.CompletedAnalysis(dataset.dir_path, job, files))
        elif job['state'] in PENDING_STATES:
            pending.append(app.collection.PendingAnalysis(dataset.dir_path, job))
    return completed, pending

def get_new_completed_analyses(dataset: app.datasets.Dataset) -> list[app.collection.CompletedAnalysis]:
    '''Use Job table to identify new jobs and return a
    CompletedAnalysis for each successful new job.
    '''
    jobs = app.smrtlink.get_dataset_jobs(dataset.id)
    staged_ids = app.state.Job.select(app.state.Job.id).execute()
    new_jobs = [j for j in jobs if j['id'] not in staged_ids]
    analyses = []
    for job in new_jobs:
        if job['state'] is SUCCESSFUL:
            files = app.smrtlink.get_job_files(job['id'])
            analyses.append(app.collection.CompletedAnalysis(dataset.dir_path, job, files))
    return analyses

def _get_analyses(jobs):
    '''Returns a tuple of completed and pending analyses
    '''
    completed = []
    pending = []
    for job in jobs:
        dataset_ids = app.smrtlink.get_job_datasets(job['id'])
        for dataset_id in dataset_ids:
            if job['state'] in FAIL_STATES:
                continue 
            dataset = app.state.Dataset.get_by_id(dataset_id)
            if job['state'] is SUCCESSFUL:
                files = app.smrtlink.get_job_files(job['id'])
                completed.append(app.collection.CompletedAnalysis(dataset.dir_path, job, files))
            elif job['state'] in PENDING_STATES:
                pending.append(app.collection.PendingAnalysis(dataset.dir_path, job))
            else:
                raise ValueError(f"Unexpected job state: {job['state']}")
    return completed, pending

def get_new_analyses():
    '''Collect all jobs created after the last update and belonging
    to any project other than project 1.
    '''
    try:
        jobs = app.smrtlink.get_jobs_created_after(app.state.LastJobUpdate.time())
        completed, pending = _get_analyses(jobs)
        latest_timestamp = sorted([job['createdAt'] for job in jobs])[-1]
        app.state.LastJobUpdate.set(latest_timestamp) # only update if _get_analyses is successful
        return completed, pending
    except Exception as e:
        raise Exception(f'Cannot get new analyses: {e}')

MAX_POLLING_TIME = 86400
POLL_RATE = 30

def _poll(analysis: app.collection.PendingAnalysis) -> app.collection.CompletedAnalysis | None:
    '''Return the completed analysis if successful, None otherwise.
    '''
    t_start = time.time()
    while True:
        job = app.smrtlink.get_job(analysis.id)
        if not job:
            app.logger.error(f'Cannot handle job {analysis.id}: Job not found in SMRT Link.')
            return
        if job["state"] is SUCCESSFUL:
            files = app.smrtlink.get_job_files(job['id'])
            return analysis.complete(files)
        if job["state"] in FAIL_STATES:
            return
        t_current = time.time()
        if t_current - t_start > MAX_POLLING_TIME:
            app.logger.error(f"Failed to handle analysis {analysis.id}: Max polling time ({MAX_POLLING_TIME}s) exceeded.")
            return
        time.sleep(POLL_RATE)

def track(pending_analyses):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(_poll, analysis) for analysis in pending_analyses}
        
    for future in concurrent.futures.as_completed(futures):
        analysis = future.result()
        if analysis is not None:
            yield analysis