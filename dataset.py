from pbcore.io.dataset.DataSetIO import DataSet
from pbcore.io.dataset.DataSetMembers import ExternalResource

def get_file_path(res, file_paths):
    if hasattr(res, 'resourceId'):
        file_paths.append(res.resourceId)
    if type(res) is ExternalResource: # else is FileIndex
        if len(res.indices) > 0:
            get_file_paths(res.indices, file_paths)
        if len(res.externalResources) > 0:
            get_file_paths(res.externalResources, file_paths)
    return file_paths

def get_file_paths(resources, file_paths):
    for res in resources:
        get_file_path(res, file_paths)
    return file_paths

def get_dataset_files(xml_file):
    ds = DataSet(xml_file)
    primary_files = get_file_paths(ds.externalResources, [])
    supplemental_files = get_file_paths(ds.supplementalResources, [])
    # ...
    return []

class DnascDataSet:
    '''
    XML Schema definitions found at https://github.com/PacificBiosciences/PacBioFileFormats 
    - ExternalResources, SupplementalResources is found in PacBioBaseDataModel.xsd
    - DataSet and derivative types are found in PacBioDatasets.xsd
    '''
    def __init__(self, uuid, xml_file, name, num_children):
        self.uuid = uuid
        self.name = name
        self.is_super = num_children > 0
        self.files = get_dataset_files(xml_file)