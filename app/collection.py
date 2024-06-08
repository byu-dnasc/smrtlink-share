import abc
import os

import app.xml

class FileCollection(abc.ABC):
    @property
    @abc.abstractmethod
    def files(self) -> list[str]:
        pass

    @property
    @abc.abstractmethod
    def _dir_name(self) -> str:
        '''Return the name of the directory where this dataset should be staged.'''
        pass

    @property
    @abc.abstractmethod
    def _prefix(self) -> str:
        '''
        Return the path prefix of the directory where this dataset should be staged.

        The default implementation returns an empty string, which is appropriate
        for when the FileCollection's directory should be located directly within
        the project directory.
        '''
        return ''

    @property
    def dir_path(self) -> str: # this method is meant to be inherited by all subclasses
        '''Return the path to the directory where this dataset should be staged.'''
        return os.path.join(self._prefix, self._dir_name)

class PendingAnalysis:
    def __init__(self, parent_dir: str, job: dict):
        self._parent_dir = parent_dir
        self._job = job
    
    def complete(self, files):
        '''Return a CompletedAnalysis object for this analysis.'''
        return CompletedAnalysis(self._parent_dir, self._job, files)
    
class CompletedAnalysis(FileCollection):
    def __init__(self, parent_dir: str, job: dict, files: list):
        self._parent_dir = parent_dir
        self._name = job['name']
        self._id = job['id']
        self._files = files
    
    @property
    def _prefix(self):
        return self._parent_dir
   
    @property
    def _dir_name(self):
        return f'Analysis {self._id}: {self._name}'
    
    @property
    def files(self):
        return self._files

class SupplementalResources(FileCollection):
    def __init__(self, parent_dir, files):
        self._parent_dir = parent_dir
        self._files = files
    
    @property
    def _prefix(self):
        return self._parent_dir
    
    @property
    def _dir_name(self):
        return 'Supplemental Run Data'

    @property
    def files(self):
        return self._files

class Dataset(FileCollection, app.BaseDataset):

    def __new__(cls, *args, **kwargs):
        '''Instantiate a Dataset or Parent, depending on the number of children.
        '''
        if 'numChildren' in kwargs and kwargs['numChildren'] > 0:
            return super(Dataset, cls).__new__(Parent)
        else: 
            return super(Dataset, cls).__new__(cls)

    def __init__(self, **kwargs):
        self._uuid = kwargs['uuid']
        self._xml = app.xml.DatasetXml(kwargs['path'])
        self._name = kwargs['name']
        if 'parentUuid' in kwargs:
            self._name = app.xml.get_sample_name(self._xml)
        self._movie_id = app.xml.get_movie_id(self._xml)
    
    @property
    def uuid(self):
        return self._uuid
    
    @property
    def _prefix(self):
        return super()._prefix # empty string

    @property
    def _dir_name(self):
        return f'Movie {self._movie_id} - {self._name}'
    
    @property
    def files(self):
        return app.xml.resources_to_file_paths(self._xml.externalResources)

    def __str__(self):
        return str(self._name)

class Parent(Dataset):
    '''
    Files belonging to a Parent dataset come only from the supplementalResources
    section of the dataset XML because the externalResources section contains
    only references to child datasets.
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._name = app.xml.get_well_sample_name(self.xml)
        self._num_children = kwargs['numChildren']
        child_dataset_dicts = app.xml.get_child_dataset_dicts(self.xml)
        self.child_datasets = []
        for child_dict in child_dataset_dicts:
            try:
                dataset = Child(self._dir_name, **child_dict) 
            except Exception as e:
                app.logger.error(f"Cannot handle SMRT Link dataset {child_dict['id']}: {e}.")
                continue
            self.child_datasets.append(dataset)
        self.child_datasets.append(app.collection.SupplementalResources(self._dir_name, self.files))

    @property
    def _prefix(self):
        return super()._prefix
    
    @property
    def _dir_name(self):
        return f'{super()._dir_name} ({self._num_children} barcoded samples)'
    
    @property
    def files(self):
        return [] # Parent datasets have no files of their own
    
class Child(Dataset):
    '''
    A child dataset is considered a dataset whose parent is in the project. 
    This implies that a project may have a dataset whose parent is not in the 
    project, but that the dataset will be represented by an instance of Dataset, 
    not of Child. In other words, a child is only a child if its parent is in the 
    project.
    '''
    def __init__(self, parent_dir, **kwargs):
        super().__init__(**kwargs)
        self._barcode = app.xml.get_barcode(self.xml)
        self._name = app.xml.get_sample_name(self.xml) # replace DataSet name with BioSample name
        self._parent_dir = parent_dir
    
    @property
    def _prefix(self):
        return self._parent_dir

    @property
    def _dir_name(self):
        return f'{self._name} ({self._barcode})'