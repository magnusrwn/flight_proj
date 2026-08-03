from pathlib import Path
import sys
import unittest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.models.base_models import FuncResponse
from src.utils import is_in_table_

class UtilsTests(unittest.TestCase):
    def test_is_in_table__name_err(self):
        r = is_in_table_(
            table_name="airport_data_ERR",
            column="code",
            airprot_code="JFK"
        )
        self.assertEqual(r.ok, False)

    def test_is_in_table__clean_input(self):
        r = is_in_table_(
            table_name="airport_data",
            column="code",
            airprot_code="JFK"
        )
        self.assertTrue(r.ok)

    def test_is_in_table__correct_input_no_airport(self):
        r = is_in_table_(
            table_name="airport_data",
            column="code",
            airprot_code="EDI"
        )
        self.assertTrue(r.ok)
         

if __name__ == '__main__':
    unittest.main()