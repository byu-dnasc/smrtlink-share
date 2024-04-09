from tests.conftest import get_project_dicts
from app.smrtlink import _dict_to_project
import app.project as project

def test_project():
    proj_dicts = get_project_dicts()
    proj = _dict_to_project(proj_dicts[1])
    assert proj