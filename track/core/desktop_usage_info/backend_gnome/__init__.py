"""Backend for GNOME Shell on Wayland. Everything goes over the session bus via
`gdbus` (part of glib, present on every GNOME system): idle time from Mutter,
the focused window from the "Window Calls Extended" shell extension
(window-calls-extended@hseliger.eu), which has to be installed and enabled.
"""

import ast
import re
import subprocess
from typing import Any, Tuple

from .. import ToolError

# gdbus prints GVariant text, e.g. `(uint64 32,)` or `('Firefox',)`. Minus the
# numeric type prefixes that is a Python tuple literal.
_TYPE_PREFIX = re.compile(r"\b(u?int(16|32|64)|byte|double|handle) ")


def gdbus_call(dest: str, path: str, method: str) -> Tuple[Any, ...]:
    """Run `gdbus call` and return the reply tuple"""
    try:
        result = subprocess.run(
            ["gdbus", "call", "--session", "--dest", dest, "--object-path", path, "--method", method],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ToolError("could not run gdbus: %s" % exc) from exc
    if result.returncode != 0:
        raise ToolError("%s failed: %s" % (method, result.stderr.strip()))
    try:
        return ast.literal_eval(_TYPE_PREFIX.sub("", result.stdout.strip()))
    except (ValueError, SyntaxError) as exc:
        raise ToolError("unexpected reply from %s: %r" % (method, result.stdout)) from exc
