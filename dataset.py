from pbcore.io.dataset.DataSetIO import DataSet
from pbcore.io.dataset.DataSetMembers import ExternalResource, ExternalResources

def get_file_path(res, file_paths):
    '''
    Get the file path of a resource and recurse if it has 
    ExternalResources
    '''
    if hasattr(res, 'resourceId'):
        file_paths.append(res.resourceId)
    if type(res) is ExternalResource: # else is FileIndex
        if len(res.indices) > 0:
            get_file_paths(res.indices, file_paths)
        if len(res.externalResources) > 0:
            get_file_paths(res.externalResources, file_paths)
    return file_paths

def get_file_paths(resources: ExternalResources, file_paths):
    '''Recursively get all file paths from a list of resources'''
    for res in resources:
        get_file_path(res, file_paths)
    return file_paths

def resources_to_file_paths(resources: ExternalResources):
    '''
    Get all file paths from DataSet.externalResources or DataSet.supplementalResources,
    regardless of the number of nodes in the underlying XML tree by using recursion.
    XML Schema definitions found at https://github.com/PacificBiosciences/PacBioFileFormats 
    - ExternalResources, SupplementalResources is found in PacBioBaseDataModel.xsd
    - DataSet and derivative types are found in PacBioDatasets.xsd
    '''
    return get_file_paths(resources, [])

def get_dataset_files(xml_file) -> list[str]:
    '''Returns all files associated with a dataset XML file.'''
    ds = DataSet(xml_file)
    primary_files = resources_to_file_paths(ds.externalResources)
    try: # TODO: how to handle split datasets?
        assert len(primary_files) == 1, f'Expected one primary file for dataset, found {len(primary_files)}'
    except AssertionError:
        pass
    supplemental_files = resources_to_file_paths(ds.supplementalResources)
    return primary_files + supplemental_files

def get_sample_xml(sample_res: ExternalResource):
    # one of the resource's externalResources is the sample XML
    xml_files = [res for res in sample_res.externalResources if res.resourceId.endswith('.xml')]
    try:
        assert xml_files, 'No XML file found in sample resource'
        return xml_files[0]
    except AssertionError:
        return None

def get_dataset_files_super(xml_file):
    ds = DataSet(xml_file)
    # in a super dataset, the externalResources represent samples 
    # and have their own XML files
    for sample_res in ds.externalResources:
        # ignore any files associated with this resource except the sample XML
        sample_dataset_xml = get_sample_xml(sample_res)
        # instead, use the files from the sample dataset XML
        sample_dataset_files = get_dataset_files(sample_dataset_xml)

class DnascDataSet:
    def __init__(self, uuid, xml_file, name, num_children):
        self.uuid = uuid
        self.name = name
        self.is_super = num_children > 0
        if self.is_super:
            self.files = get_dataset_files_super(xml_file, num_children)
        else:
            self.files = get_dataset_files(xml_file)