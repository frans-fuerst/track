import os

class TrackServerError(Exception):
    pass

class WindowInformationError(TrackServerError):
    pass

class ToolError(TrackServerError):
    pass

if os.name == 'posix':
    from .backend_x11 import idle
    from .backend_x11 import applicationinfo
elif os.name == 'nt':
    from .backend_windows import idle
    from .backend_windows import applicationinfo
else:
    raise Exception("currenty only 'posix' and 'win' are supported systems")
