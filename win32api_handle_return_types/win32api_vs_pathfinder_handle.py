import struct
import win32api
from cuda.pathfinder import load_nvidia_dynamic_lib

POINTER_ADDRESS_SPACE = 2 ** (struct.calcsize("P") * 8)


def s2u(handle_sint):
    return handle_sint + POINTER_ADDRESS_SPACE if handle_sint < 0 else handle_sint


def u2s(handle_uint):
    return handle_uint - POINTER_ADDRESS_SPACE if handle_uint >= POINTER_ADDRESS_SPACE // 2 else handle_uint


loaded_dl = load_nvidia_dynamic_lib("cublasLt")
print(loaded_dl)
print(f"{type(loaded_dl._handle_uint)=} {loaded_dl._handle_uint} {u2s(loaded_dl._handle_uint)}")

dll_name = loaded_dl.abs_path

GetModuleHandle_return = win32api.GetModuleHandle(dll_name)
print(f"{type(GetModuleHandle_return)=} {GetModuleHandle_return} {s2u(GetModuleHandle_return)}")

LOAD_LIBRARY_SEARCH_DEFAULT_DIRS = 0x00001000
LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR = 0x00000100
LoadLibraryEx_return = win32api.LoadLibraryEx(dll_name, 0, LOAD_LIBRARY_SEARCH_DEFAULT_DIRS | LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR)
print(f"{type(LoadLibraryEx_return)=}, {LoadLibraryEx_return} {s2u(LoadLibraryEx_return)}")

LoadLibrary_return = win32api.LoadLibrary(dll_name)
print(f"{type(LoadLibrary_return)=}, {LoadLibrary_return} {s2u(LoadLibrary_return)}")
