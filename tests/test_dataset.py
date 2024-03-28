import os
import dataset

def test_pbcore_dataset():
    username = os.environ.get('USER')
    path = f'/home/{username}/smrtlink-container/data/L9j.pacb'
    xml_path = f'{path}/pb_formats/m84100_240301_194028_s1.hifi_reads.consensusreadset.xml'
    ds = dataset.DataSet(xml_path)
    sample_datasets = []
    for xml in [res.resourceId for res in ds.externalResources if res.resourceId.endswith('.xml')]: # FIXME: implement function to get XMLs from external resources
        assert os.path.exists(xml)
        sample_datasets.append(dataset.DataSet(xml))
    assert True