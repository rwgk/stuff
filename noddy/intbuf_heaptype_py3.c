#include <Python.h>

typedef struct {
    PyObject_HEAD
    int* buf;
} intbuf_IntBufObject;

static PyModuleDef intbufmodule = {
    PyModuleDef_HEAD_INIT,
    "intbuf",
    "Example module that creates an extension type.",
    -1,
    NULL, NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC
PyInit_intbuf(void)
{
    PyObject* m;

    m = PyModule_Create(&intbufmodule);
    if (m == NULL)
        return NULL;

    PyHeapTypeObject *heap_type =
        (PyHeapTypeObject *) PyType_Type.tp_alloc(&PyType_Type, 0);
    if (!heap_type)
        return NULL;
    heap_type->ht_name = (PyObject *) PyUnicode_FromString("intbuf.IntBuf");
    heap_type->ht_qualname = (PyObject *) PyUnicode_FromString("intbuf.IntBuf");
    PyTypeObject *nt = &heap_type->ht_type;
    nt->tp_name = "intbuf.IntBuf";
    nt->tp_basicsize = sizeof(intbuf_IntBufObject);
    nt->tp_flags = Py_TPFLAGS_DEFAULT |
                   Py_TPFLAGS_BASETYPE |
                   Py_TPFLAGS_HEAPTYPE;
    nt->tp_doc = "IntBuf objects";
    if (PyType_Ready(nt) < 0)
        return NULL;

    PyModule_AddObject(m, "IntBuf", (PyObject *) nt);
    return m;
}
