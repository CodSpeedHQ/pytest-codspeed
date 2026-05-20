#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "core.h"

/* Capsule destructor for InstrumentHooks pointer */
static void instrument_hooks_capsule_destructor(PyObject *capsule) {
    InstrumentHooks *hooks = (InstrumentHooks *)PyCapsule_GetPointer(capsule, "instrument_hooks");
    if (hooks) {
        instrument_hooks_deinit(hooks);
    }
}

/* instrument_hooks_init() -> capsule */
static PyObject *py_instrument_hooks_init(PyObject *self, PyObject *args) {
    InstrumentHooks *hooks = instrument_hooks_init();
    if (!hooks) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to initialize instrument hooks");
        return NULL;
    }
    return PyCapsule_New(hooks, "instrument_hooks", instrument_hooks_capsule_destructor);
}

/* instrument_hooks_is_instrumented(capsule) -> bool */
static PyObject *py_instrument_hooks_is_instrumented(PyObject *self, PyObject *args) {
    PyObject *capsule;
    if (!PyArg_ParseTuple(args, "O", &capsule)) {
        return NULL;
    }

    InstrumentHooks *hooks = (InstrumentHooks *)PyCapsule_GetPointer(capsule, "instrument_hooks");
    if (!hooks) {
        return NULL;
    }

    bool result = instrument_hooks_is_instrumented(hooks);
    return PyBool_FromLong(result);
}

/* instrument_hooks_start_benchmark(capsule) -> int */
static PyObject *py_instrument_hooks_start_benchmark(PyObject *self, PyObject *args) {
    PyObject *capsule;
    if (!PyArg_ParseTuple(args, "O", &capsule)) {
        return NULL;
    }

    InstrumentHooks *hooks = (InstrumentHooks *)PyCapsule_GetPointer(capsule, "instrument_hooks");
    if (!hooks) {
        return NULL;
    }

    uint8_t result = instrument_hooks_start_benchmark(hooks);
    return PyLong_FromLong(result);
}

/* instrument_hooks_stop_benchmark(capsule) -> int */
static PyObject *py_instrument_hooks_stop_benchmark(PyObject *self, PyObject *args) {
    PyObject *capsule;
    if (!PyArg_ParseTuple(args, "O", &capsule)) {
        return NULL;
    }

    InstrumentHooks *hooks = (InstrumentHooks *)PyCapsule_GetPointer(capsule, "instrument_hooks");
    if (!hooks) {
        return NULL;
    }

    uint8_t result = instrument_hooks_stop_benchmark(hooks);
    return PyLong_FromLong(result);
}

/* instrument_hooks_set_executed_benchmark(capsule, pid, uri) -> int */
static PyObject *py_instrument_hooks_set_executed_benchmark(PyObject *self, PyObject *args) {
    PyObject *capsule;
    int32_t pid;
    const char *uri;

    if (!PyArg_ParseTuple(args, "Oiy", &capsule, &pid, &uri)) {
        return NULL;
    }

    InstrumentHooks *hooks = (InstrumentHooks *)PyCapsule_GetPointer(capsule, "instrument_hooks");
    if (!hooks) {
        return NULL;
    }

    uint8_t result = instrument_hooks_set_executed_benchmark(hooks, pid, uri);
    return PyLong_FromLong(result);
}

/* instrument_hooks_set_integration(capsule, name, version) -> int */
static PyObject *py_instrument_hooks_set_integration(PyObject *self, PyObject *args) {
    PyObject *capsule;
    const char *name;
    const char *version;

    if (!PyArg_ParseTuple(args, "Oyy", &capsule, &name, &version)) {
        return NULL;
    }

    InstrumentHooks *hooks = (InstrumentHooks *)PyCapsule_GetPointer(capsule, "instrument_hooks");
    if (!hooks) {
        return NULL;
    }

    uint8_t result = instrument_hooks_set_integration(hooks, name, version);
    return PyLong_FromLong(result);
}

/* instrument_hooks_add_marker(capsule, pid, marker_type, timestamp) -> int */
static PyObject *py_instrument_hooks_add_marker(PyObject *self, PyObject *args) {
    PyObject *capsule;
    int32_t pid;
    unsigned char marker_type;
    uint64_t timestamp;

    if (!PyArg_ParseTuple(args, "OibK", &capsule, &pid, &marker_type, &timestamp)) {
        return NULL;
    }

    InstrumentHooks *hooks = (InstrumentHooks *)PyCapsule_GetPointer(capsule, "instrument_hooks");
    if (!hooks) {
        return NULL;
    }

    uint8_t result = instrument_hooks_add_marker(hooks, pid, marker_type, timestamp);
    return PyLong_FromLong(result);
}

/* instrument_hooks_current_timestamp() -> int */
static PyObject *py_instrument_hooks_current_timestamp(PyObject *self, PyObject *args) {
    uint64_t result = instrument_hooks_current_timestamp();
    return PyLong_FromUnsignedLongLong(result);
}

/* callgrind_start_instrumentation() -> None */
static PyObject *py_callgrind_start_instrumentation(PyObject *self, PyObject *args) {
    callgrind_start_instrumentation();
    Py_RETURN_NONE;
}

/* callgrind_stop_instrumentation() -> None */
static PyObject *py_callgrind_stop_instrumentation(PyObject *self, PyObject *args) {
    callgrind_stop_instrumentation();
    Py_RETURN_NONE;
}

/* instrument_hooks_set_feature(feature, enabled) -> None */
static PyObject *py_instrument_hooks_set_feature(PyObject *self, PyObject *args) {
    unsigned long long feature;
    int enabled;

    if (!PyArg_ParseTuple(args, "Kp", &feature, &enabled)) {
        return NULL;
    }

    instrument_hooks_set_feature((uint64_t)feature, (bool)enabled);
    Py_RETURN_NONE;
}

/* instrument_hooks_set_environment(capsule, section_name, key, value) -> int */
static PyObject *py_instrument_hooks_set_environment(PyObject *self, PyObject *args) {
    PyObject *capsule;
    const char *section_name;
    const char *key;
    const char *value;

    if (!PyArg_ParseTuple(args, "Oyyy", &capsule, &section_name, &key, &value)) {
        return NULL;
    }

    InstrumentHooks *hooks = (InstrumentHooks *)PyCapsule_GetPointer(capsule, "instrument_hooks");
    if (!hooks) {
        return NULL;
    }

    uint8_t result = instrument_hooks_set_environment(hooks, section_name, key, value);
    return PyLong_FromLong(result);
}

/* instrument_hooks_set_environment_list(capsule, section_name, key, values) -> int */
static PyObject *py_instrument_hooks_set_environment_list(PyObject *self, PyObject *args) {
    PyObject *capsule;
    const char *section_name;
    const char *key;
    PyObject *values_list;

    if (!PyArg_ParseTuple(args, "OyyO", &capsule, &section_name, &key, &values_list)) {
        return NULL;
    }

    if (!PyList_Check(values_list) && !PyTuple_Check(values_list)) {
        PyErr_SetString(PyExc_TypeError, "values must be a list or tuple of bytes");
        return NULL;
    }

    InstrumentHooks *hooks = (InstrumentHooks *)PyCapsule_GetPointer(capsule, "instrument_hooks");
    if (!hooks) {
        return NULL;
    }

    Py_ssize_t count = PySequence_Fast_GET_SIZE(values_list);
    const char **c_values = NULL;
    if (count > 0) {
        c_values = PyMem_Malloc(sizeof(const char *) * count);
        if (!c_values) {
            PyErr_NoMemory();
            return NULL;
        }

        for (Py_ssize_t i = 0; i < count; i++) {
            PyObject *item = PySequence_Fast_GET_ITEM(values_list, i);
            if (!PyBytes_Check(item)) {
                PyMem_Free(c_values);
                PyErr_SetString(PyExc_TypeError, "values must contain bytes objects");
                return NULL;
            }
            c_values[i] = PyBytes_AsString(item);
        }
    }

    uint8_t result = instrument_hooks_set_environment_list(
        hooks, section_name, key, c_values, (uint32_t)count);
    PyMem_Free(c_values);
    return PyLong_FromLong(result);
}

/* instrument_hooks_write_environment(capsule, pid) -> int */
static PyObject *py_instrument_hooks_write_environment(PyObject *self, PyObject *args) {
    PyObject *capsule;
    int32_t pid;

    if (!PyArg_ParseTuple(args, "Oi", &capsule, &pid)) {
        return NULL;
    }

    InstrumentHooks *hooks = (InstrumentHooks *)PyCapsule_GetPointer(capsule, "instrument_hooks");
    if (!hooks) {
        return NULL;
    }

    uint8_t result = instrument_hooks_write_environment(hooks, pid);
    return PyLong_FromLong(result);
}

/* callgrind_add_obj_skip(path: bytes) -> int */
static PyObject *py_callgrind_add_obj_skip(PyObject *self, PyObject *args) {
    const char *path;
    if (!PyArg_ParseTuple(args, "y", &path)) {
        return NULL;
    }
    uint8_t result = instrument_hooks_callgrind_add_obj_skip(path);
    return PyLong_FromLong(result);
}

/* Method definitions */
static PyMethodDef InstrumentHooksMethods[] = {
    {"instrument_hooks_init", py_instrument_hooks_init, METH_NOARGS,
     "Initialize instrument hooks and return a handle."},
    {"instrument_hooks_is_instrumented", py_instrument_hooks_is_instrumented, METH_VARARGS,
     "Check if instrumentation is active."},
    {"instrument_hooks_start_benchmark", py_instrument_hooks_start_benchmark, METH_VARARGS,
     "Start a benchmark measurement."},
    {"instrument_hooks_stop_benchmark", py_instrument_hooks_stop_benchmark, METH_VARARGS,
     "Stop a benchmark measurement."},
    {"instrument_hooks_set_executed_benchmark", py_instrument_hooks_set_executed_benchmark, METH_VARARGS,
     "Set the executed benchmark URI and PID."},
    {"instrument_hooks_set_integration", py_instrument_hooks_set_integration, METH_VARARGS,
     "Set the integration name and version."},
    {"instrument_hooks_add_marker", py_instrument_hooks_add_marker, METH_VARARGS,
     "Add a marker to the instrumentation."},
    {"instrument_hooks_current_timestamp", py_instrument_hooks_current_timestamp, METH_NOARGS,
     "Get the current timestamp."},
    {"callgrind_start_instrumentation", py_callgrind_start_instrumentation, METH_NOARGS,
     "Start callgrind instrumentation."},
    {"callgrind_stop_instrumentation", py_callgrind_stop_instrumentation, METH_NOARGS,
     "Stop callgrind instrumentation."},
    {"instrument_hooks_set_feature", py_instrument_hooks_set_feature, METH_VARARGS,
     "Set a feature flag in the instrument hooks library."},
    {"instrument_hooks_set_environment", py_instrument_hooks_set_environment, METH_VARARGS,
     "Register a key-value pair under a named section for environment collection."},
    {"instrument_hooks_set_environment_list", py_instrument_hooks_set_environment_list, METH_VARARGS,
     "Register a list of values under a named section for environment collection."},
    {"instrument_hooks_write_environment", py_instrument_hooks_write_environment, METH_VARARGS,
     "Flush all registered environment sections to disk."},
    {"callgrind_add_obj_skip", py_callgrind_add_obj_skip, METH_VARARGS,
     "Tell callgrind to skip the given object file path."},
    {NULL, NULL, 0, NULL}
};

/* Module definition */
static struct PyModuleDef instrument_hooks_module = {
    PyModuleDef_HEAD_INIT,
    "dist_instrument_hooks",
    "Native Python bindings for instrument hooks library",
    -1,
    InstrumentHooksMethods
};

/* Module initialization */
PyMODINIT_FUNC PyInit_dist_instrument_hooks(void) {
    PyObject *module = PyModule_Create(&instrument_hooks_module);
    if (module == NULL) {
        return NULL;
    }

    /* Add constants */
    PyModule_AddIntConstant(module, "MARKER_TYPE_SAMPLE_START", MARKER_TYPE_SAMPLE_START);
    PyModule_AddIntConstant(module, "MARKER_TYPE_SAMPLE_END", MARKER_TYPE_SAMPLE_END);
    PyModule_AddIntConstant(module, "MARKER_TYPE_BENCHMARK_START", MARKER_TYPE_BENCHMARK_START);
    PyModule_AddIntConstant(module, "MARKER_TYPE_BENCHMARK_END", MARKER_TYPE_BENCHMARK_END);
    PyModule_AddIntConstant(module, "FEATURE_DISABLE_CALLGRIND_MARKERS", FEATURE_DISABLE_CALLGRIND_MARKERS);

#ifdef Py_GIL_DISABLED
    PyUnstable_Module_SetGIL(module, Py_MOD_GIL_NOT_USED);
#endif

    return module;
}
