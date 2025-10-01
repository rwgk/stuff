from __future__ import annotations

import ctypes
from ctypes import (
    CDLL,
    Structure,
    POINTER,
    byref,
    c_void_p,
    c_int,
    c_size_t,
    c_uint,
    c_char_p,
    create_string_buffer,
)
import ctypes.util
import os


# glibc dlinfo request codes
RTLD_DI_SERINFO = 4
RTLD_DI_SERINFOSIZE = 5

# flags for dlopen
RTLD_NOW = getattr(os, "RTLD_NOW", 2)

# Structs mirror <dlfcn.h>
class Dl_serpath(Structure):
    _fields_ = [
        ("dls_name", c_char_p),
        ("dls_flags", c_uint),
    ]


class Dl_serinfo_header(Structure):
    """
    Header-only view (no trailing array).
    We'll re-cast the buffer to a full struct with the right array length later.
    """
    _fields_ = [
        ("dls_size", c_size_t),
        ("dls_cnt", c_uint),
        # No dls_serpath here; we only use this to read size/cnt safely.
    ]


def _load_libdl():
    name = ctypes.util.find_library("dl") or "libdl.so.2"
    return CDLL(name)


def _get_symbols():
    libdl = _load_libdl()

    # int dlinfo(void *handle, int request, void *p);
    dlinfo = libdl.dlinfo
    dlinfo.argtypes = [c_void_p, c_int, c_void_p]
    dlinfo.restype = c_int

    # void *dlopen(const char *filename, int flag);
    dlopen = libdl.dlopen
    dlopen.argtypes = [c_char_p, c_int]
    dlopen.restype = c_void_p

    # char *dlerror(void);
    dlerror = libdl.dlerror
    dlerror.argtypes = []
    dlerror.restype = c_char_p

    return dlinfo, dlopen, dlerror


def get_rtld_search_dirs() -> list[str]:
    """
    Return the glibc dynamic linker's directory search list (in order),
    without loading any new library. Linux/glibc only.
    """
    dlinfo, dlopen, dlerror = _get_symbols()

    # Use a real handle: dlopen(NULL, RTLD_NOW) -> main program handle
    handle = dlopen(None, RTLD_NOW)
    if not handle:
        err = dlerror() or b"unknown dlopen error"
        raise OSError(f"dlopen(NULL) failed: {err.decode()}")

    # 1) Ask for sizes
    hdr = Dl_serinfo_header()
    rc = dlinfo(handle, RTLD_DI_SERINFOSIZE, byref(hdr))
    if rc != 0:
        err = dlerror()
        raise OSError(f"dlinfo(SERINFOSIZE) failed: {(err or b'rc!=0').decode()}")

    size_needed = hdr.dls_size
    cnt = hdr.dls_cnt
    if size_needed < ctypes.sizeof(Dl_serinfo_header) or cnt == 0:
        # It’s valid for cnt to be 0 in degenerate cases, but usually it’s >0.
        # We’ll allow 0 (return empty list).
        if cnt == 0:
            return []

    # 2) Allocate exactly the size glibc asked for
    buf = create_string_buffer(size_needed)

    # Define a struct type with the correct array length
    class Dl_serinfo_full(Structure):
        _fields_ = [
            ("dls_size", c_size_t),
            ("dls_cnt", c_uint),
            ("dls_serpath", Dl_serpath * cnt),
        ]

    pinfo = ctypes.cast(buf, POINTER(Dl_serinfo_full))

    # Initialize header fields that glibc expects set
    pinfo.contents.dls_size = size_needed
    pinfo.contents.dls_cnt = cnt

    # (Optional) Some examples call SERINFOSIZE again with the full buffer
    rc = dlinfo(handle, RTLD_DI_SERINFOSIZE, pinfo)
    if rc != 0:
        err = dlerror()
        raise OSError(f"dlinfo(SERINFOSIZE, buf) failed: {(err or b'rc!=0').decode()}")

    # 3) Fill the buffer with the actual paths
    rc = dlinfo(handle, RTLD_DI_SERINFO, pinfo)
    if rc != 0:
        err = dlerror()
        raise OSError(f"dlinfo(SERINFO) failed: {(err or b'rc!=0').decode()}")

    out: list[str] = []
    cnt = pinfo.contents.dls_cnt  # read back in case it changed
    for i in range(cnt):
        name_ptr = pinfo.contents.dls_serpath[i].dls_name
        if name_ptr:
            out.append(ctypes.cast(name_ptr, c_char_p).value.decode())
    return out


if __name__ == "__main__":
    dirs = get_rtld_search_dirs()
    print("RTLD search dirs:")
    for d in dirs:
        print("  ", d)
