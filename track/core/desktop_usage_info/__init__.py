import os


class TrackServerError(Exception):
    pass


class WindowInformationError(TrackServerError):
    pass


class ToolError(TrackServerError):
    pass


if os.name == "posix":
    from .backend_x11 import applicationinfo, idle
elif os.name == "nt":
    from .backend_windows import applicationinfo, idle
else:
    raise Exception("currenty only 'posix' and 'win' are supported systems")
