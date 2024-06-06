from pbcore.io.dataset.DataSetIO import DataSet as DatasetXml
from pbcore.io.dataset.DataSetMembers import ExternalResource, ExternalResources

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

def resources_to_file_paths(resources: ExternalResources):
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
    primary_files = resources_to_file_paths(ds.externalResources)
    try: # TODO: how to handle split datasets?
        assert len(primary_files) == 1, f'Expected one resource file for dataset, found {len(primary_files)}'
    except AssertionError:
        pass
    supplemental_files = resources_to_file_paths(ds.supplementalResources)
    return primary_files + supplemental_files

def _get_xml(xml_res: ExternalResource):
    # one of the resource's externalResources is the sample XML
    xml_files = [res.resourceId for res in xml_res.externalResources if res.resourceId.endswith('.xml')]
    assert xml_files, 'No XML file found in externalResource'
    return xml_files[0]

def get_child_dataset_dicts(parent_xml):
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