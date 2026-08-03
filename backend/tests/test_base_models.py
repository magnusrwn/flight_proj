from pathlib import Path
import sys
import unittest
from typing import Any
from pydantic import BaseModel, ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.models.base_models import SendFlightRequest


class BaseModelError(Exception):
    """Base exception for pydantic BaseModel faliures"""
class BaseModelFieldCountError(BaseModelError):
    """Raised when field count exceeds the number of fields in the BaseModel"""

# Helper funcs
def collect_schema_path(item, paths=None, path="") -> set[str]:
    '''
    Reccursively searches handed-in data
    returning a set of all paths/ ends to the data
    '''
    if paths == None:
        paths = set()

    if isinstance(item, dict):
        for key, child in item.items():
            dict_path = f"{path}.{key}" if path else key
            paths.add(dict_path)
            collect_schema_path(child, paths, dict_path)

    elif isinstance(item, list):
        list_path = f"{path}[]"
        paths.add(list_path)
        for i in item:
            collect_schema_path(i, paths, list_path)
    return paths

def collect_model_path(model: type[BaseModel], paths=None, path="") -> set[str]:
    if paths == None:
        paths = set()

    for f_name, f_info in model.model_fields.items():
        model_path = f"{path}.{f_name}" if path else f_name
        paths.add(model_path)

        f_type = f_info.annotation
        if isinstance(f_type, type) and issubclass(f_type, BaseModel):
            collect_model_path(model=f_info, paths=paths, path=model_path)
    return paths

def test_field_numbers(schema:list[dict[str, Any]], base_model:type[BaseModel]) -> None:
    schema_explored_set = collect_schema_path(item=schema)
    model_explored_set = collect_model_path(model=base_model)

    if len(schema_explored_set) != len(model_explored_set):
        raise BaseModelFieldCountError

def test_schema_fields(schema:list[dict[str, Any]], base_model:type[BaseModel]):
    for i in schema:
        base_model(**i)

# Test
class BaseModelTests(unittest.TestCase):
    def test_field_count(self) -> None:
        schema = [
            {"depIataCode":"EDI","data":"2026-08-29"},
        ]

        with self.assertRaises(BaseModelFieldCountError):
            test_field_numbers(schema, SendFlightRequest)

    def test_fields(self) -> None:
        schema = [
            {"depIataCode":"EDI", "date":"2026-08-29", "car":"no"},
            {"depIataCode":"LYS", "date":"2026-08-29"}
        ]

        with self.assertRaises(ValidationError) as ctx:
            test_schema_fields(schema, SendFlightRequest)

        # Uncomment when you want to test for specific errs
        # errors = ctx.exception.errors()
        # self.assertEqual(errors[0]["loc"], ("car",))


if __name__ == '__main__':
    unittest.main()