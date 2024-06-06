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
        app.state.Job.insert(id=analysis.id).execute()
    for completed_analysis in app.job.track(pending):
        app.filesystem.stage(completed_analysis)
        app.state.Job.insert(id=analysis.id).execute()

def _get_removed_datasets(project_id, dataset_data):
    current_ids = [ds['uuid'] for ds in dataset_data]
    return (app.state.Dataset
                    .select()
                    .where(app.state.Dataset.project_id == project_id,
                            app.state.Dataset.id.not_in(current_ids)
                    .execute()))

def _handle_removed_datasets(project_id, dataset_data):
    datasets_to_remove = _get_removed_datasets(project_id, dataset_data)
    for dataset in datasets_to_remove:
        app.filesystem.remove(dataset)
        app.globus.remove_permissions(dataset.id)

def _handle_dataset_analyses(dataset: app.collection.Dataset):
    try:
        completed, pending = app.job.get_analyses(dataset)
    except Exception as e:
        app.logger.error(f'Failed to get new analyses: {e}')
        return
    _stage_analyses(completed, pending)

def _handle_existing_dataset(project_id, dataset, member_ids, new_member_ids):
    if dataset.project_id == project_id: # visited
        for member_id in new_member_ids:
            app.globus.create_permission(dataset, member_id)
    else: # reassigned
        app.globus.remove_permissions(dataset.id)
        for member_id in member_ids:
            app.globus.create_permission(dataset, member_id)
        dataset.project_id = project_id
        dataset.save()

def _handle_new_dataset(project_id, dataset_d, member_ids):
    try:
        dataset = app.collection.Dataset(**dataset_d)
    except Exception as e:
        app.logger.error(f"Cannot handle SMRT Link dataset {dataset_d['id']}: {e}.")
        return None
    if app.filesystem.stage(dataset):
        for member_id in member_ids:
            permission_id = app.globus.create_permission(dataset, member_id)
            (app.state.Permission.insert(member_id=member_id,
                                        dataset_id=dataset.id,
                                        permission_id=permission_id)
                                .execute())
        (app.state.Dataset.insert(project_id=project_id,
                                        id=dataset.id,
                                        staging_dir=dataset.dir_path)
                                .execute())
        return dataset
    return None

def _handle_datasets(project_id, dataset_data, member_ids, new_member_ids):
    datasets = []
    for dataset_d in dataset_data:
        dataset = app.state.Dataset.get_or_none(app.state.Dataset.id == dataset_d['uuid'])
        if dataset is None:
            dataset = _handle_new_dataset(project_id, dataset_d, member_ids)
            if dataset:
                _handle_dataset_analyses(dataset)
                if type(dataset) is app.collection.Parent:
                    for child in dataset.child_datasets:
                        app.filesystem.stage(child)
        else: # dataset is app.state.Dataset
            _handle_existing_dataset(project_id, dataset, member_ids, new_member_ids)
            for analysis in app.job.get_new_completed_analyses(dataset):
                if app.filesystem.stage(analysis): # This staging is redundant, but is intended as a backup in case the app did not receive a notification for a new analysis.
                    app.state.Job.insert(id=analysis.id).execute()
        datasets.append(dataset)        
    return datasets

def _get_removed_members(project_id, members) -> list[app.state.ProjectMember]:
    current_ids = [m.member_id for m in members]
    return (app.state.ProjectMember
                    .select()
                    .where(app.state.ProjectMember.project_id == project_id,
                            app.state.ProjectMember.member_id
                                                    .not_in(current_ids))
                    .execute())

def _handle_removed_members(project_id, member_ids, datasets):
    removed_members = _get_removed_members(project_id, member_ids)
    for member in removed_members:
        for dataset in datasets:
            app.globus.remove_permission(dataset.id, member.member_id)
        member.delete_instance()

def _handle_new_members(project_id, member_ids):
    new_members = []
    for member_id in member_ids:
        project_member = app.state.ProjectMember.get_or_none(app.state.ProjectMember.project_id == project_id,
                                            app.state.ProjectMember.member_id == member_id)
        if project_member is None:
            new_members.append(member_id)
            app.state.ProjectMember.insert(project_id=project_id, member_id=member_id).execute()
    return new_members

def _handle_project(project_id, project_dataset_data, member_ids):
    new_member_ids = _handle_new_members(project_id, member_ids)
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
    datasets = (app.state.Dataset.select()
                                .where(app.state.Dataset.project_id == project_id)
                                .execute())
    for dataset in datasets:
        app.filesystem.remove(dataset)
        app.globus.remove_permissions(dataset.id)
        dataset.delete_instance()

def new_analyses():
    try:
        pending_analyses, completed_analyses = app.job.get_new_analyses()
    except Exception as e:
        app.logger.error(f'Failed to update analyses: {e}')
        return
    _stage_analyses(completed_analyses, pending_analyses)