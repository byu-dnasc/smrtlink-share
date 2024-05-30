import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app import logger
from app.collection import PendingAnalysis, CompletedAnalysis
import app.smrtlink as smrtlink
from app.state import LastJobUpdate, JobId

FAIL_STATES = {'FAILED', 'TERMINATED', 'ABORTED'}
PENDING_STATES = {'CREATED', 'SUBMITTED', 'RUNNING'}
SUCCESSFUL = 'SUCCESSFUL'

def get_new_project_analyses(project_id):
    jobs = smrtlink.get_project_analyses(project_id)
    staged_ids = JobId.select().execute()
    new_jobs = [j for j in jobs if j['id'] not in staged_ids]
    for job in new_jobs:
        dataset_ids = smrtlink.get_job_datasets(job['id'])
        for dataset_id in dataset_ids:
            if job['state'] is SUCCESSFUL:
                files = smrtlink.get_job_files(job['id'])
                yield CompletedAnalysis(dataset_id, job, files)

def _get_analyses(jobs):
    '''Returns a tuple of completed and pending analyses
    '''
    completed = []
    pending = []
    for job in jobs:
        dataset_ids = smrtlink.get_job_datasets(job['id'])
        for dataset_id in dataset_ids:
            if job['state'] in FAIL_STATES:
                continue 
            files = smrtlink.get_job_files(job['id'])
            if job['state'] is SUCCESSFUL:
                completed.append(CompletedAnalysis(dataset_id, job, files))
            elif job['state'] in PENDING_STATES:
                pending.append(PendingAnalysis(dataset_id, job, files))
            else:
                raise ValueError(f"Unexpected job state: {job['state']}")
    return completed, pending

def get_new_analyses():
    '''Collect all jobs created after the last update and belonging
    to any project other than project 1.
    '''
    try:
        jobs = smrtlink.get_jobs_created_after(LastJobUpdate.time())
        completed, pending = _get_analyses(jobs)
        latest_timestamp = sorted([job['createdAt'] for job in jobs])[-1]
        LastJobUpdate.set(latest_timestamp) # only update if _get_analyses is successful
        return completed, pending
    except Exception as e:
        raise Exception(f'Cannot get new analyses: {e}')

def get_project_analyses(project_id):
    '''Returns a tuple of completed and pending analyses for a project.
    '''
    try:
        jobs = smrtlink.get_project_analyses(project_id)
        return _get_analyses(jobs)
    except Exception as e:
        raise Exception(f'Cannot get project {project_id} analyses: {e}')

MAX_POLLING_TIME = 86400
POLL_RATE = 30

def _poll(analysis: PendingAnalysis):
    '''Return the completed analysis if successful, None otherwise.
    '''
    t_start = time.time()
    while True:
        job = smrtlink.get_job(analysis.id)
        if not job:
            logger.error(f'Cannot handle job {analysis.id}: Job not found in SMRT Link.')
            return
        state = job["state"]
        if state in (SUCCESSFUL, FAIL_STATES):
            break
        t_current = time.time()
        if t_current - t_start > MAX_POLLING_TIME:
            logger.error(f"Failed to handle analysis {analysis.id}: Max polling time ({MAX_POLLING_TIME}s) exceeded.")
            return
        time.sleep(POLL_RATE)
    if state is SUCCESSFUL:
        return analysis.complete(job)
    return None

def track(pending_analyses):
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(_poll, analysis) for analysis in pending_analyses}
        
    for future in as_completed(futures):
        analysis = future.result()
        if analysis is not None:
            yield analysis