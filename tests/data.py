from tests.test_collection import TOMATO_PARENT

PROJECT = {
    "id": 1,
    "name": "Tomato Project",
    "datasets": [
      {
        "id": 1,
        "name": "Germany tomato 20 and 21-Cell1 (all samples)",
        "numChildren": 2,
        "uuid": "48a71a3e-c97c-43ea-ba41-8c2b31dd32b2",
        "path": TOMATO_PARENT
      }
    ],
    "members": [
      {
        "login": "admin",
        "role": "OWNER"
      },
      {
        "login": "superawesomeuser",
        "role": "CAN_VIEW"
      }
    ]
}

PROJECT_1 = {
  'id':1,
  'name':'project name',
  'datasets':[
    {
      'id': 1,
      'name': 'dataset name',
      'uuid': 'a',
      'path': TOMATO_PARENT
    }
  ],
  "members": [
    {
      "login": "admin",
      "role": "OWNER"
    },
    {
      "login": "superawesomeuser",
      "role": "CAN_VIEW"
    }
  ]
}