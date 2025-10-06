# distutils: language = c
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True

from libc.stdlib cimport malloc, free
from libc.stddef cimport size_t
from posix.unistd cimport usleep

cdef extern from "mockcuda.h":
    void mockcuda_init()
    void mockcuda_shutdown()
    void mockcuda_free(void* p) nogil

ctypedef struct Resource:
    void*  data
    size_t nbytes

cdef Resource* alloc_resource(size_t nbytes):
    cdef Resource* r = <Resource*> malloc(sizeof(Resource))
    if r == NULL:
        return NULL
    r.nbytes = nbytes
    r.data = malloc(nbytes)
    return r

# --- Bad: releases the GIL in __dealloc__ (will crash eventually) ---
cdef class WrapperNogil:
    cdef Resource* r
    def __cinit__(self):
        self.r = NULL

    @staticmethod
    cdef WrapperNogil from_resource(Resource* r):
        cdef WrapperNogil w = WrapperNogil.__new__(WrapperNogil)
        w.r = r
        return w

    def __dealloc__(self):
        cdef Resource* r = self.r
        if r != NULL:
            # Releasing the GIL here is the bug. Two __dealloc__ calls can overlap.
            with nogil:
                if r.data != NULL:
                    # Simulate non-trivial driver work and widen the race window
                    usleep(50000)          # 50 ms
                    mockcuda_free(r.data)  # both threads can free the same pointer
                    r.data = NULL          # set-to-NULL happens after free (check-then-act race)
            self.r = NULL  # leak r itself to keep the demo focused on the data-pointer race

# --- Good: keeps the GIL in __dealloc__ (no crash in practice) ---
cdef class WrapperWithGIL:
    cdef Resource* r
    def __cinit__(self):
        self.r = NULL

    @staticmethod
    cdef WrapperWithGIL from_resource(Resource* r):
        cdef WrapperWithGIL w = WrapperWithGIL.__new__(WrapperWithGIL)
        w.r = r
        return w

    def __dealloc__(self):
        cdef Resource* r = self.r
        if r != NULL:
            # Identical logic, but DO NOT release the GIL.
            if r.data != NULL:
                usleep(50000)          # still fine: C call, but we keep the GIL
                mockcuda_free(r.data)
                r.data = NULL
        self.r = NULL

def make_twins_nogil(size_t nbytes):
    """Return two wrappers *owning the same resource* -> race if dealloc overlaps."""
    cdef Resource* r = alloc_resource(nbytes)
    if r == NULL or r.data == NULL:
        raise MemoryError
    return WrapperNogil.from_resource(r), WrapperNogil.from_resource(r)

def make_twins_with_gil(size_t nbytes):
    cdef Resource* r = alloc_resource(nbytes)
    if r == NULL or r.data == NULL:
        raise MemoryError
    return WrapperWithGIL.from_resource(r), WrapperWithGIL.from_resource(r)

def start_driver():
    mockcuda_init()

def stop_driver():
    mockcuda_shutdown()
