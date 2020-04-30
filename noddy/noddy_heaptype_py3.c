#include <Python.h>

typedef struct {
    PyObject_HEAD
    /* Type-specific fields go here. */
} noddy_NoddyObject;

static PyModuleDef noddymodule = {
    PyModuleDef_HEAD_INIT,
    "noddy",
    "Example module that creates an extension type.",
    -1,
    NULL, NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC
PyInit_noddy(void)
{
    PyObject* m;

    m = PyModule_Create(&noddymodule);
    if (m == NULL)
        return NULL;

    PyHeapTypeObject *heap_type =
        (PyHeapTypeObject *) PyType_Type.tp_alloc(&PyType_Type, 0);
    if (!heap_type)
        return NULL;
    heap_type->ht_name = (PyObject *) PyUnicode_FromString("noddy.Noddy");
    heap_type->ht_qualname = (PyObject *) PyUnicode_FromString("noddy.Noddy");
    PyTypeObject *nt = &heap_type->ht_type;
    nt->tp_name = "noddy.Noddy";
    nt->tp_basicsize = sizeof(noddy_NoddyObject);
    nt->tp_flags = Py_TPFLAGS_DEFAULT |
                   Py_TPFLAGS_BASETYPE |
                   Py_TPFLAGS_HEAPTYPE;
    nt->tp_doc = "Noddy objects";
    if (PyType_Ready(nt) < 0)
        return NULL;
    Py_INCREF(nt);  /* For PyModule_AddObject to steal. */
    PyModule_AddObject(m, "Noddy", (PyObject *) nt);
    return m;
}
