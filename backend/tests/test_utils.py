from pathlib import Path
import sys
import unittest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.utils import is_in_table

class UtilsTests(unittest.TestCase):
    def test_is_in_table__name_err(self):
        r = is_in_table(
            table_name="weather_req_table_ERR_TABLE_NAME",
            column="code",
            airprot_code="JFK"
        )
        self.assertFalse(r.ok)

    def test_is_in_table__clean_input(self):
        r = is_in_table(
            table_name="weather_req_table",
            column="code",
            airprot_code="JFK"
        )
        self.assertTrue(r.ok)

    def test_is_in_table_correct__input_no_airport(self):
        r = is_in_table(
            table_name="weather_req_table",
            column="code",
            airprot_code="LHR"
        )
        self.assertFalse(r.data)
         

if __name__ == '__main__':
    unittest.main()