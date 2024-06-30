'''
This module is where everything happens. It imports most of the rest
of the app's modules and uses them to get data from SMRT Link, update
the app's state, create a remove files, and create and remove Globus 
permissions.
'''
import typing

import app.filesystem
import app.collection
import app.smrtlink
import app.globus
import app.state
import app.job
import app

def expired_permissions():
    """Bring the app's database of permissions up to date by removing
    the records of any permissions that should be expired."""
    app.state.Permission.remove_expired()

def _stage_analyses(completed, pending):
    '''
    Stage completed analyses, and track pending analyses.
    '''
    for analysis in completed:
        app.filesystem.stage(analysis)
    for completed_analysis in app.job.track(pending):
        app.filesystem.stage(completed_analysis)

def _handle_removed_datasets(project_id, dataset_dicts):
    current_ids = [ds['uuid'] for ds in dataset_dicts]
    removed_datasets = app.state.Dataset.get_removed_datasets(project_id, current_ids)
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

def _handle_new_dataset(dataset_d) -> typing.Union[app.collection.Dataset, None]:
    try:
        dataset = app.collection.Dataset(**dataset_d)
    except Exception as e:
        app.logger.error(f"Cannot handle SMRT Link dataset {dataset_d['uuid']}: {e}.")
        return None
    if app.filesystem.stage(dataset):
        app.state.Dataset.insert(project_id=dataset_d['projectId'],
                                 uuid=dataset_d['uuid'],
                                 dir_path=dataset.dir_path).execute()
        _handle_dataset_analyses(dataset)
        if type(dataset) is app.collection.Parent:
            for child in dataset.child_datasets:
                if app.filesystem.stage(child):
                    _handle_dataset_analyses(child)
        return dataset
    return None

def _handle_current_datasets(dataset_dicts) -> list[app.BaseDataset]:
    '''
    Get or create BaseDataset instances and update app state with respect to 
    datasets. State updates include adding new datasets and updating the 
    `project_id` of reassigned (existing) datasets.
    '''
    datasets = []
    reassigned_dataset_uuids = []
    for dataset_d in dataset_dicts:
        dataset = app.state.Dataset.get_by_dataset_uuid(dataset_d['uuid'])
        if dataset is None:
            dataset = _handle_new_dataset(dataset_d)
        else: 
            if dataset.project_id is not dataset_d['projectId']:
                reassigned_dataset_uuids.append(dataset.uuid)
                dataset.update_project_id(dataset_d['projectId'])
        if dataset is not None:
            datasets.append(dataset)
    return datasets, reassigned_dataset_uuids

def _handle_removed_members(project_id, member_ids, datasets: list[app.BaseDataset]):
    removed_members = app.state.ProjectMember.get_removed_members(project_id, member_ids)
    for member in removed_members:
        for dataset in datasets:
            app.globus.remove_permission(dataset.uuid, dataset.dir_path, member.member_id)
        member.delete_instance()

def _handle_current_members(project_id, member_ids):
    '''
    Update app state with respect to project members. Return the list of
    project members which have been added to the project since the last update.
    '''
    new_members = []
    for member_id in member_ids:
        if app.state.ProjectMember.exists(project_id, member_id):
            new_members.append(member_id)
        else:
            app.state.ProjectMember.insert(project_id=project_id, member_id=member_id).execute()
    return new_members

def _handle_permissions(datasets, reassigned_dataset_ids, member_ids, new_member_ids):
    for dataset in datasets:
        if type(dataset) is app.state.Dataset:
            members_to_add = new_member_ids
            if dataset.uuid in reassigned_dataset_ids:
                app.globus.remove_permissions(dataset)
                members_to_add = member_ids
            for member in members_to_add:
                app.globus.create_permission(dataset.uuid, dataset.dir_path, member)
        elif type(dataset) is app.collection.Dataset:
            for member in member_ids:
                app.globus.create_permission(dataset.uuid, dataset.dir_path, member)
        else:
            ...

def _handle_project(project_id: int, dataset_dicts: list[dict], member_ids: list[str]):
    project_datasets, reassigned_dataset_uuids = _handle_current_datasets(dataset_dicts)
    new_member_ids = _handle_current_members(project_id, member_ids)
    _handle_removed_datasets(project_id, dataset_dicts)
    _handle_removed_members(project_id, member_ids, project_datasets)
    _handle_permissions(project_datasets, reassigned_dataset_uuids, member_ids, new_member_ids)

def updated_project(project_id):
    try:
        dataset_dicts, member_ids = app.smrtlink.get_project(project_id)
        _handle_project(project_id, dataset_dicts, member_ids)
    except Exception as e:
        app.logger.error(f'Failed to handle update to project {project_id}: {e}')
        return

def new_project():
    try:
        project_id, dataset_dicts, member_ids = app.smrtlink.get_new_project()
        _handle_project(project_id, dataset_dicts, member_ids)
    except Exception as e:
        app.logger.error(f'Failed to handle new project: {e}')
        return

def deleted_project(project_id):
    datasets = app.state.Dataset.get_by_project_id(project_id)
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