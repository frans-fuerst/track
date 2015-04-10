import os

if os.name == 'posix':
    import desktop_usage_info.backend_x11.idle
    import desktop_usage_info.backend_x11.applicationinfo
    idle = desktop_usage_info.backend_x11.idle
    applicationinfo = desktop_usage_info.backend_x11.applicationinfo
elif os.name == 'nt':
    import desktop_usage_info.backend_windows.idle
    import desktop_usage_info.backend_windows.applicationinfo
    idle = desktop_usage_info.backend_windows.idle
    applicationinfo = desktop_usage_info.backend_windows.applicationinfo
else:
    raise Exception("currenty only 'posix' and 'win' are supported systems")

#__all__ = desktop_usage_info.backend_x11.__all__
#print __all__

