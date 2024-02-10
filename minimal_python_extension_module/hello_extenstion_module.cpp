#include <Python.h>

namespace {

static PyObject *wrapHelloWorld(PyObject *, PyObject *) {
    return PyUnicode_FromString("Hello from a Python extension module.");
}

static PyMethodDef ThisMethodDef[]
    = {{"HelloWorld", wrapHelloWorld, METH_NOARGS, "HelloWorld() -> str"},
       {nullptr, nullptr, 0, nullptr}};

static struct PyModuleDef ThisModuleDef = {
    PyModuleDef_HEAD_INIT,     // m_base
    "hello_extenstion_module", // m_name
    nullptr,                   // m_doc
    -1,                        // m_size
    ThisMethodDef,             // m_methods
    nullptr,                   // m_slots
    nullptr,                   // m_traverse
    nullptr,                   // m_clear
    nullptr                    // m_free
};

} // namespace

extern "C" PyObject *PyInit_hello_extenstion_module() { return PyModule_Create(&ThisModuleDef); }
