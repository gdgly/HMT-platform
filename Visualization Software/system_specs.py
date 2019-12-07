import sys
import os
import ctypes
import _winreg

### Globals ###
MB = 1048576
GB = 1073741824

def get_registry_value(key, subkey, value):
    if sys.platform != 'win32':
        raise OSError("get_registry_value is only supported on Windows")
    
    key = getattr(_winreg, key)
    handle = _winreg.OpenKey(key, subkey)
    try:
        (value, type) = _winreg.QueryValueEx(handle, value)
        return value
    except:
        return None


class SystemInformation:
    def __init__(self):
        self.os = self._os_version().strip()
        self.cpu = self._cpu().strip()
        self.totalRam, self.availableRam = self._ram()
        self.totalRam = self.totalRam / MB
        self.availableRam = self.availableRam / MB
        self.hdFree = self._disk_c() / GB
    
    def _os_version(self):
        def get(key):
            return get_registry_value("HKEY_LOCAL_MACHINE",
                "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion", key)
        os = get("ProductName")
        sp = get("CSDVersion")
        build = get("CurrentBuildNumber")
        return "%s %s (build %s)" % (os, sp, build)
    
    def _cpu(self):
        return get_registry_value(
            "HKEY_LOCAL_MACHINE", 
            "HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0",
            "ProcessorNameString")
    
    def _ram(self):
        kernel32 = ctypes.windll.kernel32
        c_ulong = ctypes.c_ulong
        class MEMORYSTATUS(ctypes.Structure):
            _fields_ = [
                ('dwLength', c_ulong),
                ('dwMemoryLoad', c_ulong),
                ('dwTotalPhys', c_ulong),
                ('dwAvailPhys', c_ulong),
                ('dwTotalPageFile', c_ulong),
                ('dwAvailPageFile', c_ulong),
                ('dwTotalVirtual', c_ulong),
                ('dwAvailVirtual', c_ulong)
            ]
        
        memoryStatus = MEMORYSTATUS()
        memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUS)
        kernel32.GlobalMemoryStatus(ctypes.byref(memoryStatus))
        return (memoryStatus.dwTotalPhys, memoryStatus.dwAvailPhys)
    
    def _disk_c(self):
        drive = os.getenv("SystemDrive")
        freeuser = ctypes.c_int64()
        total = ctypes.c_int64()
        free = ctypes.c_int64()
        try:
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(unicode(drive),
                ctypes.byref(freeuser), ctypes.byref(total), ctypes.byref(free))
        except:
            try:
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(drive,
                    ctypes.byref(freeuser), ctypes.byref(total),
                    ctypes.byref(free))
            except:
                raise ctypes.WinError()
        return freeuser.value

if __name__ == "__main__":
    s = SystemInformation()
    print s.os
    print s.cpu
    print "RAM : %dMB total" % s.totalRam
    print "RAM : %dMB free" % s.availableRam
    print "System HD : %dGB free" % s.hdFree
