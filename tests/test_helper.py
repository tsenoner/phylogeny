import unittest

import pandas as pd

from src.helper import add_column_before


class TestAddColumnBefore(unittest.TestCase):
    def setUp(self):
        # Setup sample data for testing
        self.data1 = pd.DataFrame(
            {
                "uid": [1, 2, 3],
                "existing_column1": [10, 20, 30],
                "existing_column2": [100, 200, 300],
            }
        )

        self.data2 = pd.DataFrame({"uid": [1, 2, 3], "new_column": ["A", "B", "C"]})

    def test_column_insertion(self):
        # Call the function
        result = add_column_before(
            self.data1, self.data2, "new_column", "existing_column2", "uid"
        )

        # Check if the column is correctly inserted
        self.assertIn("new_column", result.columns)
        self.assertEqual(
            list(result.columns),
            ["uid", "existing_column1", "new_column", "existing_column2"],
        )

        # Check if the values are merged correctly
        expected_values = pd.Series(["A", "B", "C"], name="new_column")
        pd.testing.assert_series_equal(
            result["new_column"], expected_values, check_names=False
        )


if __name__ == "__main__":
    unittest.main()
