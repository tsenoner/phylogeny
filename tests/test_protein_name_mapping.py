import json
import unittest

from src.prot_family.protein_name_mapping import dpp_protein_mapping


class TestProteinNameGrouping(unittest.TestCase):
    def setUp(self):
        self.dpp_protein_mapping = dpp_protein_mapping

    def test_group_protein_names(self):
        with open("tests/data/dpp_protein_name_mapping.json") as f:
            test_data = json.load(f)

        for expected_group, names in test_data.items():
            with self.subTest(expected_group=expected_group):
                for name in names:
                    self.assertEqual(self.dpp_protein_mapping(name), expected_group)


if __name__ == "__main__":
    unittest.main()
