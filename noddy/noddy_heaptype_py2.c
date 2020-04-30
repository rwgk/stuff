#include <Python.h>

typedef struct {
    PyObject_HEAD
    /* Type-specific fields go here. */
} noddy_NoddyObject;

static PyMethodDef noddy_methods[] = {
    {NULL}  /* Sentinel */
};

#ifndef PyMODINIT_FUNC /* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initnoddy(void)
{
    PyObject* m;

    m = Py_InitModule3("noddy", noddy_methods,
                       "Example module that creates an extension type.");
    if (m == NULL)
        return;

    PyHeapTypeObject *heap_type =
        (PyHeapTypeObject *) PyType_Type.tp_alloc(&PyType_Type, 0);
    if (!heap_type)
        return;
    heap_type->ht_name = (PyObject *) PyString_FromString("noddy.Noddy");
    PyTypeObject *nt = &heap_type->ht_type;
    nt->tp_name = "noddy.Noddy";
    nt->tp_basicsize = sizeof(noddy_NoddyObject);
    nt->tp_flags = Py_TPFLAGS_DEFAULT |
                   Py_TPFLAGS_CHECKTYPES |
                   Py_TPFLAGS_BASETYPE |
                   Py_TPFLAGS_HEAPTYPE;
    nt->tp_doc = "Noddy objects";
    if (PyType_Ready(nt) < 0)
        return;
    Py_INCREF(nt);  /* For PyModule_AddObject to steal. */
    PyModule_AddObject(m, "Noddy", (PyObject *) nt);
}
