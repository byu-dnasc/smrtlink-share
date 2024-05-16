from app.collection import Analysis
import app.smrtlink as smrtlink
from app.state import AnalysisModel

def _get_job_project_dataset(job_id):
    rows = (AnalysisModel.select(AnalysisModel.project_id,
                                 AnalysisModel.dataset_id)
                         .where(AnalysisModel.analysis_id == job_id)
                         .execute())
    if not rows:
        return None
    for row in rows:
        yield row.project_id, row.dataset_id

def get_analyses(datasets, project_id):
    for ds in datasets:
        jobs = smrtlink.get_dataset_jobs(ds.id)
        ids_to_ignore = (AnalysisModel.select(AnalysisModel.analysis_id)
                                      .where(AnalysisModel.dataset_id == ds.id,
                                             AnalysisModel.project_id == project_id)
                                      .execute())
        for job_d in [j for j in jobs if j['id'] not in ids_to_ignore]:
            if job_d['state'] == 'SUCCESSFUL':
                files = smrtlink.get_job_files(job_d['id'])
                yield Analysis(ds.dir_path, 
                                job_d['name'], 
                                job_d['id'], 
                                files)

def get_new(created_after):
    query = 'gte:' + created_after
    jobs = smrtlink.CLIENT.get_analysis_jobs(createdAt=query)
    job_d = jobs[0]