# This file was automatically generated by SWIG (http://www.swig.org).
# Version 3.0.8
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.





from sys import version_info
if version_info >= (2, 6, 0):
    def swig_import_helper():
        from os.path import dirname
        import imp
        fp = None
        try:
            fp, pathname, description = imp.find_module('_edgetpu_cpp_wrapper', [dirname(__file__)])
        except ImportError:
            import _edgetpu_cpp_wrapper
            return _edgetpu_cpp_wrapper
        if fp is not None:
            try:
                _mod = imp.load_module('_edgetpu_cpp_wrapper', fp, pathname, description)
            finally:
                fp.close()
            return _mod
    _edgetpu_cpp_wrapper = swig_import_helper()
    del swig_import_helper
else:
    import _edgetpu_cpp_wrapper
del version_info
try:
    _swig_property = property
except NameError:
    pass  # Python < 2.2 doesn't have 'property'.


def _swig_setattr_nondynamic(self, class_type, name, value, static=1):
    if (name == "thisown"):
        return self.this.own(value)
    if (name == "this"):
        if type(value).__name__ == 'SwigPyObject':
            self.__dict__[name] = value
            return
    method = class_type.__swig_setmethods__.get(name, None)
    if method:
        return method(self, value)
    if (not static):
        if _newclass:
            object.__setattr__(self, name, value)
        else:
            self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)


def _swig_setattr(self, class_type, name, value):
    return _swig_setattr_nondynamic(self, class_type, name, value, 0)


def _swig_getattr_nondynamic(self, class_type, name, static=1):
    if (name == "thisown"):
        return self.this.own()
    method = class_type.__swig_getmethods__.get(name, None)
    if method:
        return method(self)
    if (not static):
        return object.__getattr__(self, name)
    else:
        raise AttributeError(name)

def _swig_getattr(self, class_type, name):
    return _swig_getattr_nondynamic(self, class_type, name, 0)


def _swig_repr(self):
    try:
        strthis = "proxy of " + self.this.__repr__()
    except Exception:
        strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)

try:
    _object = object
    _newclass = 1
except AttributeError:
    class _object:
        pass
    _newclass = 0


class SwigPyIterator(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SwigPyIterator, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SwigPyIterator, name)

    def __init__(self, *args, **kwargs):
        raise AttributeError("No constructor defined - class is abstract")
    __repr__ = _swig_repr
    __swig_destroy__ = _edgetpu_cpp_wrapper.delete_SwigPyIterator
    __del__ = lambda self: None

    def value(self):
        return _edgetpu_cpp_wrapper.SwigPyIterator_value(self)

    def incr(self, n=1):
        return _edgetpu_cpp_wrapper.SwigPyIterator_incr(self, n)

    def decr(self, n=1):
        return _edgetpu_cpp_wrapper.SwigPyIterator_decr(self, n)

    def distance(self, x):
        return _edgetpu_cpp_wrapper.SwigPyIterator_distance(self, x)

    def equal(self, x):
        return _edgetpu_cpp_wrapper.SwigPyIterator_equal(self, x)

    def copy(self):
        return _edgetpu_cpp_wrapper.SwigPyIterator_copy(self)

    def next(self):
        return _edgetpu_cpp_wrapper.SwigPyIterator_next(self)

    def __next__(self):
        return _edgetpu_cpp_wrapper.SwigPyIterator___next__(self)

    def previous(self):
        return _edgetpu_cpp_wrapper.SwigPyIterator_previous(self)

    def advance(self, n):
        return _edgetpu_cpp_wrapper.SwigPyIterator_advance(self, n)

    def __eq__(self, x):
        return _edgetpu_cpp_wrapper.SwigPyIterator___eq__(self, x)

    def __ne__(self, x):
        return _edgetpu_cpp_wrapper.SwigPyIterator___ne__(self, x)

    def __iadd__(self, n):
        return _edgetpu_cpp_wrapper.SwigPyIterator___iadd__(self, n)

    def __isub__(self, n):
        return _edgetpu_cpp_wrapper.SwigPyIterator___isub__(self, n)

    def __add__(self, n):
        return _edgetpu_cpp_wrapper.SwigPyIterator___add__(self, n)

    def __sub__(self, *args):
        return _edgetpu_cpp_wrapper.SwigPyIterator___sub__(self, *args)
    def __iter__(self):
        return self
SwigPyIterator_swigregister = _edgetpu_cpp_wrapper.SwigPyIterator_swigregister
SwigPyIterator_swigregister(SwigPyIterator)

class StringVector(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, StringVector, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, StringVector, name)
    __repr__ = _swig_repr

    def iterator(self):
        return _edgetpu_cpp_wrapper.StringVector_iterator(self)
    def __iter__(self):
        return self.iterator()

    def __nonzero__(self):
        return _edgetpu_cpp_wrapper.StringVector___nonzero__(self)

    def __bool__(self):
        return _edgetpu_cpp_wrapper.StringVector___bool__(self)

    def __len__(self):
        return _edgetpu_cpp_wrapper.StringVector___len__(self)

    def __getslice__(self, i, j):
        return _edgetpu_cpp_wrapper.StringVector___getslice__(self, i, j)

    def __setslice__(self, *args):
        return _edgetpu_cpp_wrapper.StringVector___setslice__(self, *args)

    def __delslice__(self, i, j):
        return _edgetpu_cpp_wrapper.StringVector___delslice__(self, i, j)

    def __delitem__(self, *args):
        return _edgetpu_cpp_wrapper.StringVector___delitem__(self, *args)

    def __getitem__(self, *args):
        return _edgetpu_cpp_wrapper.StringVector___getitem__(self, *args)

    def __setitem__(self, *args):
        return _edgetpu_cpp_wrapper.StringVector___setitem__(self, *args)

    def pop(self):
        return _edgetpu_cpp_wrapper.StringVector_pop(self)

    def append(self, x):
        return _edgetpu_cpp_wrapper.StringVector_append(self, x)

    def empty(self):
        return _edgetpu_cpp_wrapper.StringVector_empty(self)

    def size(self):
        return _edgetpu_cpp_wrapper.StringVector_size(self)

    def swap(self, v):
        return _edgetpu_cpp_wrapper.StringVector_swap(self, v)

    def begin(self):
        return _edgetpu_cpp_wrapper.StringVector_begin(self)

    def end(self):
        return _edgetpu_cpp_wrapper.StringVector_end(self)

    def rbegin(self):
        return _edgetpu_cpp_wrapper.StringVector_rbegin(self)

    def rend(self):
        return _edgetpu_cpp_wrapper.StringVector_rend(self)

    def clear(self):
        return _edgetpu_cpp_wrapper.StringVector_clear(self)

    def get_allocator(self):
        return _edgetpu_cpp_wrapper.StringVector_get_allocator(self)

    def pop_back(self):
        return _edgetpu_cpp_wrapper.StringVector_pop_back(self)

    def erase(self, *args):
        return _edgetpu_cpp_wrapper.StringVector_erase(self, *args)

    def __init__(self, *args):
        this = _edgetpu_cpp_wrapper.new_StringVector(*args)
        try:
            self.this.append(this)
        except Exception:
            self.this = this

    def push_back(self, x):
        return _edgetpu_cpp_wrapper.StringVector_push_back(self, x)

    def front(self):
        return _edgetpu_cpp_wrapper.StringVector_front(self)

    def back(self):
        return _edgetpu_cpp_wrapper.StringVector_back(self)

    def assign(self, n, x):
        return _edgetpu_cpp_wrapper.StringVector_assign(self, n, x)

    def resize(self, *args):
        return _edgetpu_cpp_wrapper.StringVector_resize(self, *args)

    def insert(self, *args):
        return _edgetpu_cpp_wrapper.StringVector_insert(self, *args)

    def reserve(self, n):
        return _edgetpu_cpp_wrapper.StringVector_reserve(self, n)

    def capacity(self):
        return _edgetpu_cpp_wrapper.StringVector_capacity(self)
    __swig_destroy__ = _edgetpu_cpp_wrapper.delete_StringVector
    __del__ = lambda self: None
StringVector_swigregister = _edgetpu_cpp_wrapper.StringVector_swigregister
StringVector_swigregister(StringVector)


def GetRuntimeVersion():
    """
    Returns runtime (libedgetpu.so) version.

    The version is dynamically retrieved from shared object.

    Retruns:
      string.
    """
    return _edgetpu_cpp_wrapper.GetRuntimeVersion()
class BasicEngine(_object):
    """Python wrapper for BasicEngine."""

    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, BasicEngine, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, BasicEngine, name)
    __repr__ = _swig_repr

    def __init__(self, *args):
        """
        Initializes BasicEngine with model's path.

        Args:
          model_path: [required] string.
          device_path: [optional] string, path to Edge TPU device.
                       See ListEdgeTpuPaths() for path example.

        """
        this = _edgetpu_cpp_wrapper.new_BasicEngine(*args)
        try:
            self.this.append(this)
        except Exception:
            self.this = this
    __swig_destroy__ = _edgetpu_cpp_wrapper.delete_BasicEngine
    __del__ = lambda self: None

    def RunInference(self, input):
        """
        Runs inference with given input.

        Args:
          input: 1-D numpy.array. Flattened input tensor.

        Returns:
          (latency, output_tensors). Latency is milliseconds in float while
          output_tensors is 1-D numpy.array. If there are multiple output tensors,
          it will be compressed into a 1-D array. You can use
          get_all_output_tensors_sizes, get_num_of_output_tensors and
          get_output_tensor_size to calculate the offset for each tensor.
          For example, if the model output 2 tensors with value [1, 2, 3] and
          [0.1, 0.4, 0.9], output_tesnors will be [1, 2, 3, 0.1, 0.4, 0.9].
        """
        return _edgetpu_cpp_wrapper.BasicEngine_RunInference(self, input)


    def get_input_tensor_shape(self):
        """
        Gets shape of required input tensor.

        For models trained for image  classification / detection, it's always
        (1, height, width, channels). After flatten, the 1-D array with size
        height * width channels is the required input for RunInference.

        Returns:
          1-D numpy.array.
        """
        return _edgetpu_cpp_wrapper.BasicEngine_get_input_tensor_shape(self)


    def get_all_output_tensors_sizes(self):
        """
        Gets sizes of output tensors.

        A model may ouput several tensors, but in RunInference and get_raw_output
        we'll concacate them as one. This funcion will return the sizes of original
        output tesnors, which can be used to calculate the offset.

        Returns:
          Numpy.array represents the sizes of output tensors.
        """
        return _edgetpu_cpp_wrapper.BasicEngine_get_all_output_tensors_sizes(self)


    def get_num_of_output_tensors(self):
        """
        Gets number of output tensors.

        Returns:
          An integer representing number of output tensors.
        """
        return _edgetpu_cpp_wrapper.BasicEngine_get_num_of_output_tensors(self)


    def get_output_tensor_size(self, tensor_index):
        """
        Gets size of specific output tensor.

        Args:
          tensor_index: integer, the index of the output tensor.

        Returns:
          An integer representing the size of the output tensor.
        """
        return _edgetpu_cpp_wrapper.BasicEngine_get_output_tensor_size(self, tensor_index)


    def required_input_array_size(self):
        """
        Returns required size of input array of RunInference.

        Returns:
          An integer representing the size of the input array used for RunInference.
        """
        return _edgetpu_cpp_wrapper.BasicEngine_required_input_array_size(self)


    def total_output_array_size(self):
        """
        Gets expected size of output array returned by RunInference.

        Returns:
          An integer representing the size of output_tensors returned by
          RunInference().
        """
        return _edgetpu_cpp_wrapper.BasicEngine_total_output_array_size(self)


    def model_path(self):
        """
        Gets the path of model loaded in the engine.

        Returns:
          A string representing the model file's path.
        """
        return _edgetpu_cpp_wrapper.BasicEngine_model_path(self)


    def get_raw_output(self):
        """
        Gets output_tensors of last inference.

        This can be used by higher level engines for debugging.

        Returns:
          A numpy.array.
        """
        return _edgetpu_cpp_wrapper.BasicEngine_get_raw_output(self)


    def get_inference_time(self):
        """
        Gets latency of last inference.

        This can be used by higher level engines for debugging.

        Returns:
          A float number(in milliseconds).
        """
        return _edgetpu_cpp_wrapper.BasicEngine_get_inference_time(self)


    def device_path(self):
        """
        Gets associated device path of this BasicEngine instance.

        Returns:
          A string representing corresponding Edge TPU device path.
        """
        return _edgetpu_cpp_wrapper.BasicEngine_device_path(self)

BasicEngine_swigregister = _edgetpu_cpp_wrapper.BasicEngine_swigregister
BasicEngine_swigregister(BasicEngine)
cvar = _edgetpu_cpp_wrapper.cvar
kEdgeTpuCppWrapperVersion = cvar.kEdgeTpuCppWrapperVersion
kSupportedRuntimeVersion = cvar.kSupportedRuntimeVersion

class ImprintingEngine(_object):
    """Engine used for imprinting method based transfer learning."""

    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, ImprintingEngine, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, ImprintingEngine, name)
    __repr__ = _swig_repr

    def __init__(self, model_path):
        """
        Initializes ImprintingEngine with embedding extractor/model's path.

        Args:
          model_path: string, path of the embedding extractor or the model previous
            trained with ImprintingEngine.
        """
        this = _edgetpu_cpp_wrapper.new_ImprintingEngine(model_path)
        try:
            self.this.append(this)
        except Exception:
            self.this = this

    def SaveModel(self, output_path):
        """
        Saves trained model as '.tflite' file.

        Args:
          output_path: string, ouput path of the trained model.
        """
        return _edgetpu_cpp_wrapper.ImprintingEngine_SaveModel(self, output_path)


    def Train(self, input):
        """
        Trains model with a set of images from same class.

        Args:
          input: list of numpy.array. Each numpy.array represents as a 1-D tensor
            converted from an image.

        Returns:
          int, the label_id for the class.
        """
        return _edgetpu_cpp_wrapper.ImprintingEngine_Train(self, input)

    __swig_destroy__ = _edgetpu_cpp_wrapper.delete_ImprintingEngine
    __del__ = lambda self: None
ImprintingEngine_swigregister = _edgetpu_cpp_wrapper.ImprintingEngine_swigregister
ImprintingEngine_swigregister(ImprintingEngine)


_edgetpu_cpp_wrapper.EdgeTpuState_kNone_swigconstant(_edgetpu_cpp_wrapper)
EdgeTpuState_kNone = _edgetpu_cpp_wrapper.EdgeTpuState_kNone

_edgetpu_cpp_wrapper.EdgeTpuState_kAssigned_swigconstant(_edgetpu_cpp_wrapper)
EdgeTpuState_kAssigned = _edgetpu_cpp_wrapper.EdgeTpuState_kAssigned

_edgetpu_cpp_wrapper.EdgeTpuState_kUnassigned_swigconstant(_edgetpu_cpp_wrapper)
EdgeTpuState_kUnassigned = _edgetpu_cpp_wrapper.EdgeTpuState_kUnassigned

def ListEdgeTpuPaths(state):
    """
    Lists paths of Edge TPU devices available to host.

    Args:
      state: device's current state. Can be:
             EDGE_TPU_STATE_ASSIGNED: devices that are associated with BasicEngine instance.
             EDGE_TPU_STATE_UNASSIGNED: devices that are available.
             EDGE_TPU_STATE_NONE: ASSIGNED or UNASSIGNED, all devices detected by host.

    Returns:
      tuple of strings, which represents device paths in certain state.

    """
    return _edgetpu_cpp_wrapper.ListEdgeTpuPaths(state)
# This file is compatible with both classic and new-style classes.

