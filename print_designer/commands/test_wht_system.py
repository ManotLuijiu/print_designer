"""
Test Thai WHT Preview System
============================

The legacy ``print_designer.custom.thai_wht_preview`` module was replaced by
``print_designer.custom.service_item_wht`` and
``print_designer.custom.item_wht_config``.

This script is kept so that the test discovery does not fail on the removed
import.  The active coverage lives in:

- ``print_designer/tests/test_service_item_wht.py``
- ``print_designer/tests/test_item_wht_config.py``

The previous version of this script also modified a real Customer document,
which is not acceptable inside an automated test run.
"""

import unittest


def test_wht_system():
    """Skip: the legacy Thai WHT preview module no longer exists."""
    raise unittest.SkipTest(
        "print_designer.custom.thai_wht_preview was replaced by "
        "print_designer.custom.service_item_wht / item_wht_config"
    )


if __name__ == "__main__":
    test_wht_system()
