# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
# This module is intentionally minimal so you can inspect the generated C code.

ctypedef void* CUevent  # stand-in for any handle type


cdef class Event:
    cdef CUevent _handle

    def __cinit__(self):
        self._handle = <CUevent>NULL

    cpdef close(self):
        if self._handle != NULL:
            self._handle = <CUevent>NULL

    def __dealloc__(self):
        self.close()


def make_and_touch():
    e = Event()
    e._handle = <CUevent>0x1
    e.close()
