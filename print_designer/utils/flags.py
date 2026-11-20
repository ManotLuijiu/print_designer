# Small helpers for the flag values that reach the app from a client.
#
# A whitelisted method receives its arguments from the request, so a flag
# arrives as the string "0", "false" or "no" and not as a boolean. Python
# treats every non empty string as true, so bool("0") would flip a flag that
# the user explicitly turned off. These helpers read the flag the way the
# user meant it.

from typing import Any

TRUTHY_STRINGS = frozenset({"1", "true", "yes", "on"})


def is_truthy(value: Any) -> bool:
    # Is the value one of the ways a client can say "yes"?
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value != 0

    if isinstance(value, str):
        return value.strip().lower() in TRUTHY_STRINGS

    return False
