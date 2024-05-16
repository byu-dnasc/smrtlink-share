import abc
from os.path import join
from pbcore.io.dataset.DataSetIO import DataSet as DatasetXml
from pbcore.io.dataset.DataSetMembers import ExternalResource, ExternalResources
from app import logger

def _get_file_path(res, file_paths):
    '''
    Get the file path of a resource and recurse if it has 
    ExternalResources
    '''
    if hasattr(res, 'resourceId'):
        file_paths.append(res.resourceId)
    if type(res) is ExternalResource: # else is FileIndex
        if len(res.indices) > 0:
            _get_file_paths(res.indices, file_paths)
        if len(res.externalResources) > 0:
            _get_file_paths(res.externalResources, file_paths)
    return file_paths

def _get_file_paths(resources: ExternalResources, file_paths):
    '''Recursively get all file paths from a list of resources'''
    for res in resources:
        _get_file_path(res, file_paths)
    return file_paths

def _resources_to_file_paths(resources: ExternalResources):
    '''
    Get all file paths from DataSet.externalResources or DataSet.supplementalResources,
    regardless of the number of nodes in the underlying XML tree by using recursion.
    XML Schema definitions found at https://github.com/PacificBiosciences/PacBioFileFormats 
    - ExternalResources, SupplementalResources is found in PacBioBaseDataModel.xsd
    - DataSet and derivative types are found in PacBioDatasets.xsd
    '''
    return _get_file_paths(resources, [])

def _get_dataset_files(xml_file) -> list[str]:
    '''Returns all files associated with a dataset XML file.'''
    ds = DatasetXml(xml_file)
    primary_files = _resources_to_file_paths(ds.externalResources)
    try: # TODO: how to handle split datasets?
        assert len(primary_files) == 1, f'Expected one resource file for dataset, found {len(primary_files)}'
    except AssertionError:
        pass
    supplemental_files = _resources_to_file_paths(ds.supplementalResources)
    return primary_files + supplemental_files

def _get_xml(xml_res: ExternalResource):
    # one of the resource's externalResources is the sample XML
    xml_files = [res.resourceId for res in xml_res.externalResources if res.resourceId.endswith('.xml')]
    assert xml_files, 'No XML file found in externalResource'
    return xml_files[0]

def _get_child_dataset_dicts(parent_xml):
    '''Return a list (generator) of dictionaries of dataset data'''
    for res in parent_xml.externalResources:
        subdataset_xml_file = _get_xml(res)
        child_xml = DatasetXml(subdataset_xml_file)
        yield {
            'name': child_xml.name,
            'uuid': child_xml.uuid,
            'path': subdataset_xml_file,
        }

def get_movie_id(xml: DatasetXml) -> str | None:
    return (xml.metadata['Collections']
                        ['CollectionMetadata']
                        .record['attrib']
                        ['Context'])

def get_sample_name(xml: DatasetXml) -> str | None:
    '''Get the sample name from a dataset XML file
    '''
    return (xml.metadata['Collections']
                        ['CollectionMetadata']
                        ['WellSample']
                        ['BioSamples'][0]
                        .record['attrib']
                        ['Name']
                        )

def get_well_sample_name(xml: DatasetXml) -> str | None:
    '''This is the name given to represent all DNA that was loaded
    in a cell. This name should only be used for parent datasets.
    '''
    return (xml.metadata['Collections']
                        ['CollectionMetadata']
                        ['WellSample']
                        .record['attrib']
                        ['Name'])

def get_barcode(xml: DatasetXml) -> str | None:
    try:
        return (xml.metadata['Collections']
                            ['CollectionMetadata']
                            ['WellSample']
                            ['BioSamples'][0]
                            ['DNABarcodes'][0]
                            .record['attrib']
                            ['Name'])
    except Exception as e:
        return None

class FileCollection(abc.ABC):
    @property
    @abc.abstractmethod
    def files(self) -> list[str]:
        pass

    @property
    @abc.abstractmethod
    def dir_name(self) -> str:
        '''Return the name of the directory where this dataset should be staged.'''
        pass

    @property
    @abc.abstractmethod
    def prefix(self) -> str:
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
        return join(self.prefix, self.dir_name)

class Analysis(FileCollection):
    def __init__(self, parent_dir, name, id, files):
        '''
        `parent_dir`: the directory in which the new directory for these analysis 
        files should be created.
        '''
        self.parent_dir = parent_dir
        self.name = name
        self._files = files
        self.id = id
    
    @property
    def prefix(self):
        return self.parent_dir
   
    @property
    def dir_name(self):
        return f'Analysis {self.id}: {self.name}'
    
    @property
    def files(self):
        return self._files

class Dataset(FileCollection):

    def __new__(cls, *args, **kwargs):
        '''Instantiate a Dataset or Parent, depending on the number of children.
        '''
        if 'numChildren' in kwargs and kwargs['numChildren'] > 0:
            return super(Dataset, cls).__new__(Parent)
        else: 
            return super(Dataset, cls).__new__(cls)

    def __init__(self, **kwargs):
        self.id = kwargs['uuid']
        self.xml = DatasetXml(kwargs['path'])
        self.name = kwargs['name']
        if 'parentUuid' in kwargs:
            self.name = get_sample_name(self.xml)
        self.movie_id = get_movie_id(self.xml)
    
    @property
    def prefix(self):
        return super().prefix # empty string

    @property
    def dir_name(self):
        return f'Movie {self.movie_id} - {self.name}'
    
    @property
    def files(self):
        return _resources_to_file_paths(self.xml.externalResources)

    def __str__(self):
        return str(self.name)

class Parent(Dataset):
    '''
    Files belonging to a Parent dataset come only from the supplementalResources
    section of the dataset XML because the externalResources section contains
    only references to child datasets.
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = get_well_sample_name(self.xml)
        self.num_children = kwargs['numChildren']
        child_dataset_dicts = _get_child_dataset_dicts(self.xml)
        self.child_datasets = []
        for child_dict in child_dataset_dicts:
            try:
                dataset = Child(self.dir_name, **child_dict) 
            except Exception as e:
                logger.error(f"Cannot handle SMRT Link dataset {child_dict['id']}: {e}.")
                continue
            self.child_datasets.append(dataset)
        self.child_datasets.append(SupplementalResources(self.dir_name, self.files))

    @property
    def prefix(self):
        return super().prefix
    
    @property
    def dir_name(self):
        return f'{super().dir_name} ({self.num_children} barcoded samples)'
    
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
        self.barcode = get_barcode(self.xml)
        self.name = get_sample_name(self.xml) # replace DataSet name with BioSample name
        self.parent_dir = parent_dir
    
    @property
    def prefix(self):
        return self.parent_dir

    @property
    def dir_name(self):
        return f'{self.name} ({self.barcode})'

class SupplementalResources(FileCollection):
    def __init__(self, parent_dir, files):
        self.parent_dir = parent_dir
        self._files = files
    
    @property
    def prefix(self):
        return self.parent_dir
    
    @property
    def dir_name(self):
        return 'Supplemental Run Data'

    @property
    def files(self):
        return self._files