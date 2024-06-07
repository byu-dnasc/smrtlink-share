import app.filesystem
import app.collection
import app.smrtlink
import app.globus
import app.state
import app.job
import app

def _stage_analyses(completed, pending):
    '''
    Stage completed analyses, and track pending analyses.
    '''
    for analysis in completed:
        app.filesystem.stage(analysis)
    for completed_analysis in app.job.track(pending):
        app.filesystem.stage(completed_analysis)

def _handle_removed_datasets(project_id, dataset_data):
    current_ids = [ds['uuid'] for ds in dataset_data]
    removed_datasets = app.state.Dataset.get_previous_datasets(project_id, current_ids)
    for dataset in removed_datasets:
        app.filesystem.remove(dataset)
        app.globus.remove_permissions(dataset)

def _handle_dataset_analyses(dataset: app.collection.Dataset):
    try:
        completed, pending = app.job.get_analyses(dataset)
    except Exception as e:
        app.logger.error(f'Failed to get new analyses: {e}')
        return
    _stage_analyses(completed, pending)

def _handle_existing_dataset(project_id, dataset: app.state.Dataset, member_ids, new_member_ids):
    if dataset.project_id == project_id: # visited
        for member_id in new_member_ids:
            app.globus.create_permission(dataset, member_id)
    else: # reassigned
        app.globus.remove_permissions(dataset)
        for member_id in member_ids:
            app.globus.create_permission(dataset, member_id)
        dataset.project_id = project_id
        dataset.save()

def _handle_new_dataset(project_id, dataset_d, member_ids):
    try:
        dataset = app.collection.Dataset(**dataset_d)
    except Exception as e:
        app.logger.error(f"Cannot handle SMRT Link dataset {dataset_d['id']}: {e}.")
        return
    if app.filesystem.stage(dataset):
        for member_id in member_ids:
            app.globus.create_permission(dataset, member_id)
        app.state.Dataset.add(dataset, project_id)
        _handle_dataset_analyses(dataset)
        if type(dataset) is app.collection.Parent:
            for child in dataset.child_datasets:
                if app.filesystem.stage(child):
                    _handle_dataset_analyses(child)

def _handle_datasets(project_id, dataset_data, member_ids, new_member_ids) -> list[app.state.Dataset]:
    datasets = []
    for dataset_d in dataset_data:
        dataset = app.state.Dataset.get_one(dataset_d['uuid'])
        if dataset is None:
            _handle_new_dataset(project_id, dataset_d, member_ids)
        else: # dataset is app.state.Dataset
            _handle_existing_dataset(project_id, dataset, member_ids, new_member_ids)
        datasets.append(dataset)        
    return datasets

def _handle_removed_members(project_id, member_ids, datasets):
    removed_members = app.state.ProjectMember.get_previous_members(project_id, member_ids)
    for member in removed_members:
        for dataset in datasets:
            app.globus.remove_permission(dataset, member.member_id)
        member.delete_instance()

def _save_new_members(project_id, member_ids):
    new_members = []
    for member_id in member_ids:
        project_member = app.state.ProjectMember.get_one(project_id, member_id)
        if project_member is None:
            new_members.append(member_id)
            app.state.ProjectMember.add(project_id, member_id)
    return new_members

def _handle_project(project_id, project_dataset_data, member_ids):
    new_member_ids = _save_new_members(project_id, member_ids)
    datasets = _handle_datasets(project_id, project_dataset_data, member_ids, new_member_ids)
    _handle_removed_members(project_id, member_ids, datasets)
    _handle_removed_datasets(project_dataset_data)

def updated_project(project_id):
    try:
        data = app.smrtlink.get_project(project_id)
        _handle_project(project_id, *data)
    except Exception as e:
        app.logger.error(f'Failed to handle update to project {project_id}: {e}')
        return

def new_project():
    try:
        data = app.smrtlink.get_new_project()
        _handle_project(*data)
    except Exception as e:
        app.logger.error(f'Failed to handle new project: {e}')
        return

def deleted_project(project_id):
    datasets = app.state.Dataset.get_multiple(project_id)
    for dataset in datasets:
        app.filesystem.remove(dataset)
        app.globus.remove_permissions(dataset)
        dataset.delete_instance()

def new_analyses():
    try:
        pending_analyses, completed_analyses = app.job.get_new_analyses()
    except Exception as e:
        app.logger.error(f'Failed to update analyses: {e}')
        return
    _stage_analyses(completed_analyses, pending_analyses)