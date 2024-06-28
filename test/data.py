PARENT_XML = 'test/tomatoes/pb_formats/m84100_240301_194028_s1.hifi_reads.consensusreadset.xml'
CHILD_XML_1 = 'test/tomatoes/pb_formats/m84100_240301_194028_s1.hifi_reads.bc1047.consensusreadset.xml'
CHILD_XML_2 = 'test/tomatoes/pb_formats/m84100_240301_194028_s1.hifi_reads.bc1048.consensusreadset.xml'
DATASET_XML_1 = CHILD_XML_1 # When a child's parent is not in the project, then it receives no special treatment and thus can serve as a "plain" dataset
DATASET_XML_2 = CHILD_XML_2 # When a child's parent is not in the project, then it receives no special treatment and thus can serve as a "plain" dataset

DATASET_1 = {
  'name': 'dataset 1 (type: Parent)',
  'uuid': '1',
  'numChildren': 2,
  'path': PARENT_XML
}

DATASET_2 = {
  'name': 'dataset 2 (type: Child)',
  'uuid': '2',
  'path': CHILD_XML_1
}

DATASET_3 = {
  'name': 'dataset 3 (type: Child)',
  'uuid': '3',
  'path': CHILD_XML_2
}

DATASET_4 = {
  'name': 'dataset 4 (type: Dataset)',
  'uuid': '4',
  'path': DATASET_XML_1
}

DATASET_5 = {
  'name': 'dataset 5 (type: Dataset)',
  'uuid': '5',
  'path': DATASET_XML_1
}

MEMBER_1 = {
  "login": "member1",
  "role": "OWNER"
}

MEMBER_2 = {
  "login": "member2",
  "role": "CAN_VIEW"
}