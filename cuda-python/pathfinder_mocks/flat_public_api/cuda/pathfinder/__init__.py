from cuda.pathfinder._private.nvidia_dynamic_libs import load_lib as _load_nvidia_dynamic_lib

__all__ = ["load_nvidia_dynamic_lib"]


# WITH OR WITHOUT THIS:
def load_nvidia_dynamic_lib(libname):
    return _load_nvidia_dynamic_lib(libname)
