import json
from pathlib import Path
import unittest


PACKAGE_JSON = Path(__file__).parents[2] / "package.json"


class TestFrontendDependencies(unittest.TestCase):
	def test_vue_and_pinia_are_explicitly_compatible(self):
		dependencies = json.loads(PACKAGE_JSON.read_text())["dependencies"]

		self.assertEqual(dependencies["vue"], "3.5.12")
		self.assertEqual(dependencies["pinia"], "2.3.1")


if __name__ == "__main__":
	unittest.main()
