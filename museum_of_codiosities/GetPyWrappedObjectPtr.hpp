#include <Python.h>

// Real code found in the wild, in an undisclosed location.

template <typename T>
T* GetPyWrappedObjectPtr(PyObject* py_object) {
  // This layout is common to SWIG and pybind11.
  struct PyWrappedObject {
    PyObject_HEAD;
    void* ptr;  // We want to retrieve this.
  };

  return reinterpret_cast<T*>(
      reinterpret_cast<PyWrappedObject*>(py_object)->ptr);
}
