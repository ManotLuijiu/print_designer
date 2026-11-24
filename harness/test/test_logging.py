#!/usr/bin/env python3
"""Try the logging of the print designer on a site.

The script is a manual probe, so it connects to a site only when it is run,
and it never runs at import time. The logs of the site are only cleared when
the caller asks for it, because the logs of a site are data.

    python harness/test/test_logging.py --site your_site
    python harness/test/test_logging.py --site your_site --clear
"""

import argparse
import os
import sys
from pathlib import Path

THE_BENCH = Path(__file__).resolve().parents[3]


def the_parser() -> argparse.ArgumentParser:
    """The arguments of the probe."""
    the_parser = argparse.ArgumentParser(description=__doc__)
    the_parser.add_argument(
        "--site",
        default=os.environ.get("FRAPPE_SITE"),
        help="the site of the probe",
    )
    the_parser.add_argument(
        "--clear",
        action="store_true",
        help="clear the logs of the site after the probe",
    )

    return the_parser


def main() -> int:
    """Run the probe on a site."""
    the_arguments = the_parser().parse_args()
    if not the_arguments.site:
        print("the site of the probe is not known")
        print("use --site or set FRAPPE_SITE")
        return 1

    sys.path.insert(0, str(THE_BENCH / "apps" / "frappe"))
    sys.path.insert(0, str(THE_BENCH / "apps" / "print_designer"))

    import frappe

    frappe.init(the_arguments.site)
    frappe.connect()

    from print_designer.utils.pdf_logging import (
        clear_pdf_generation_logs,
        get_pdf_generation_logs,
        log_pdf_generation_issue,
    )

    print("the logging methods are imported")

    from print_designer.logger import get_logger

    the_logger = get_logger("print_designer_test")
    the_logger.info("the test log entry of the print designer")

    print("the log entry is written")

    the_result = log_pdf_generation_issue(
        "TEST_EVENT",
        "the test message of the script",
        {"test": True, "script": "test_logging.py"},
        "INFO",
    )
    print(f"the server side logging result: {the_result}")

    print(f"the logs of the site: {get_pdf_generation_logs(10)}")

    if the_arguments.clear:
        print(f"the logs are cleared: {clear_pdf_generation_logs()}")
    else:
        print("the logs are kept, use --clear to clear them")

    frappe.db.rollback()
    frappe.destroy()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
