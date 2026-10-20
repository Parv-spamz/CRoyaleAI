"""Bounded local audit scheduling; no game or training process is changed."""
import os


def lower_own_priority():
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.GetCurrentProcess.restype=wintypes.HANDLE
        kernel.SetPriorityClass.argtypes=(wintypes.HANDLE,wintypes.DWORD)
        if not kernel.SetPriorityClass(kernel.GetCurrentProcess(),0x4000):
            raise ctypes.WinError(ctypes.get_last_error())
    else:
        os.nice(10)
