# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import copy

import pytest
from google.protobuf import wrappers_pb2 as wrappers

from bosdyn.api import image_geometry_pb2, service_customization_pb2, units_pb2
from bosdyn.client.service_customization_helpers import (InvalidCustomParamSpecError,
                                                         _BoolParamValidator, _CustomParamValidator,
                                                         _DictParamValidator, _DoubleParamValidator,
                                                         _Int64ParamValidator, _ListParamValidator,
                                                         _OneOfParamValidator,
                                                         _RegionOfInterestParamValidator,
                                                         _StringParamValidator,
                                                         create_value_validator,
                                                         dict_param_coerce_to, dict_params_to_dict,
                                                         double_param_coerce_to,
                                                         int_param_coerce_to, list_param_coerce_to,
                                                         list_params_to_list, make_bool_param_spec,
                                                         make_custom_param_spec,
                                                         make_dict_child_spec, make_dict_param_spec,
                                                         make_double_param_spec,
                                                         make_int64_param_spec,
                                                         make_list_param_spec,
                                                         make_one_of_child_spec,
                                                         make_one_of_param_spec,
                                                         make_region_of_interest_param_spec,
                                                         make_roi_service_and_source,
                                                         make_string_param_spec,
                                                         make_user_interface_info,
                                                         one_of_param_coerce_to,
                                                         oneof_param_to_dict,
                                                         string_param_coerce_to, validate_dict_spec)

# Helpers to define specs


def numerical_spec(numerical_type, default_value=None, min_value=None, max_value=None):
    spec = numerical_type.Spec()
    if default_value is not None:
        spec.default_value.value = default_value
    if min_value is not None:
        spec.min_value.value = min_value
    if max_value is not None:
        spec.max_value.value = max_value
    return spec


def string_spec(default_value=None, options=None, editable=False):
    string_spec = service_customization_pb2.StringParam.Spec()
    if default_value is not None:
        string_spec.default_value = default_value
    if options is not None:
        string_spec.options.extend(options)
    string_spec.editable = editable
    return string_spec


def bool_spec(bool_value=False):
    bool_spec = service_customization_pb2.BoolParam.Spec()
    bool_spec.default_value.CopyFrom(wrappers.BoolValue(value=bool_value))
    return bool_spec


#Not currently testing the other arguments in a meaningful way, but they can be added
def roi_spec(allows_rectangle=True):
    roi_spec = service_customization_pb2.RegionOfInterestParam.Spec()
    roi_spec.service_and_source.service = "fake_service"
    roi_spec.service_and_source.source = "fake_source"
    roi_spec.default_area.rectangle.x = 5
    roi_spec.default_area.rectangle.x = 10
    roi_spec.default_area.rectangle.cols = 5
    roi_spec.default_area.rectangle.rows = 10
    roi_spec.allows_rectangle = allows_rectangle
    return roi_spec


def custom_spec(type_string, original_spec):
    custom_spec = service_customization_pb2.CustomParam.Spec()
    spec_string = type_string + "_spec"
    getattr(custom_spec, spec_string).CopyFrom(original_spec)
    return custom_spec


def list_spec(type_string, original_spec, min_number_of_values=None, max_number_of_values=None):
    list_spec = service_customization_pb2.ListParam.Spec()
    list_spec.element_spec.CopyFrom(custom_spec(type_string, original_spec))
    if min_number_of_values:
        list_spec.min_number_of_values.value = min_number_of_values
    if max_number_of_values:
        list_spec.max_number_of_values.value = max_number_of_values
    return list_spec


def dict_spec(spec_list):
    dict_spec = service_customization_pb2.DictParam.Spec()
    for index in range(spec_list):
        dict_spec.specs["param" + index]


# Test cases are built individually in an attempt to minimize number of test cases necessary for decent coverage
# Cases should be structured with passing cases first, and failing cases second for easier indexing of good vs. bad cases

#default, min_value, max_value, is_valid
int_spec_test_cases = [
    (3, 1, 9, True),
    (-4, None, None, True),
    (None, None, None, True),
    (-8, 0, 5, False),
    (1, 3, 9, False),
    (-2, -1, None, False)
] #yapf: disable
int_spec_inputs = [(numerical_spec(service_customization_pb2.Int64Param,
                                   *inputs[0:3]), _Int64ParamValidator, inputs[-1])
                   for inputs in int_spec_test_cases]

#default, min_value, max_value, is_valid
double_spec_test_cases = [
    (0.01, -0.1, 0.9, True),
    (-.99, None, 431.6, True),
    (None, None, None, True),
    (0.6, 3.5, 9, False),
    (-5, -1, None, False)
] #yapf: disable
double_spec_inputs = [(numerical_spec(service_customization_pb2.DoubleParam,
                                      *inputs[0:3]), _DoubleParamValidator, inputs[-1])
                      for inputs in double_spec_test_cases]

#default, options, is_valid
string_spec_test_cases = [
    ("red", ["red", "blue", "green"], False, True),
    ("default", None, False, True),
    ("yellow", ["red", "blue", "green"], True, True),
    (None, None, False, True),
    ("car", ["red"], False, False)
] #yapf: disable
string_spec_inputs = [(string_spec(*inputs[0:3]), _StringParamValidator, inputs[-1])
                      for inputs in string_spec_test_cases]

#value, is_valid
bool_spec_inputs = [
    (bool_spec(bool_value), _BoolParamValidator, True) for bool_value in [True, False]
]

roi_spec_inputs = [(roi_spec(allows_rectangle), _RegionOfInterestParamValidator, allows_rectangle)
                   for allows_rectangle in [True, False]]

#type_string, element_spec, is_valid
custom_spec_test_cases = [
    ("int", int_spec_inputs[0][0], True),
    ("string", string_spec_inputs[-1][0], False)
] #yapf: disable
custom_spec_inputs = [(custom_spec(*inputs[0:-1]), _CustomParamValidator, inputs[-1])
                      for inputs in custom_spec_test_cases]

#type_string, element_spec, min_number_of_values, max_number_of_values, is_valid
list_spec_test_cases = [
    ("int", int_spec_inputs[0][0], 1, 4, True),
    ("string", string_spec_inputs[0][0], None, None, True),
    ("bool", bool_spec_inputs[0][0], 3, 2, False),
    ("int", int_spec_inputs[-1][0], 1, 4, False),
    ("roi", roi_spec_inputs[0][0], -3, -1, False)
] #yapf: disable
list_spec_inputs = [
    (list_spec(*inputs[0:4]), _ListParamValidator, inputs[-1]) for inputs in list_spec_test_cases
]


def small_dict_spec(int64_spec, string_spec):
    dict_spec = service_customization_pb2.DictParam.Spec()
    dict_spec.specs["int"].spec.int_spec.CopyFrom(int64_spec)
    dict_spec.specs["string_options"].spec.string_spec.CopyFrom(string_spec)
    return dict_spec


small_dict_spec_good = small_dict_spec(int_spec_inputs[0][0], string_spec_inputs[0][0])
small_dict_spec_bad = small_dict_spec(int_spec_inputs[-1][0], string_spec_inputs[0][0])


def small_one_of_spec(dict_spec1, dict_spec2, default_key="option 1"):
    one_of_spec = service_customization_pb2.OneOfParam.Spec()
    one_of_spec.specs["option 1"].spec.CopyFrom(dict_spec1)
    one_of_spec.specs["option 2"].spec.CopyFrom(dict_spec2)
    if default_key:
        one_of_spec.default_key = default_key
    return one_of_spec


small_one_of_spec_good = small_one_of_spec(small_dict_spec_good, small_dict_spec_good)
small_one_of_spec_bad_dict = small_one_of_spec(small_dict_spec_good, small_dict_spec_bad)
small_one_of_spec_bad_key = small_one_of_spec(small_dict_spec_good, small_dict_spec_good,
                                              "not_an_option")
small_one_of_spec_no_key = small_one_of_spec(small_dict_spec_good, small_dict_spec_good,
                                             default_key=None)


def nested_dict_spec(int_spec, double_spec, string_spec, bool_spec, roi_spec, list_spec,
                     one_of_spec, dict_spec):
    nested_dict_spec = service_customization_pb2.DictParam.Spec()
    nested_dict_spec.specs["int"].spec.int_spec.CopyFrom(int_spec)
    nested_dict_spec.specs["double"].spec.double_spec.CopyFrom(double_spec)
    nested_dict_spec.specs["string"].spec.string_spec.CopyFrom(string_spec)
    nested_dict_spec.specs["bool"].spec.bool_spec.CopyFrom(bool_spec)
    nested_dict_spec.specs["roi"].spec.roi_spec.CopyFrom(roi_spec)
    nested_dict_spec.specs["list"].spec.list_spec.CopyFrom(list_spec)
    nested_dict_spec.specs["one_of"].spec.one_of_spec.CopyFrom(one_of_spec)
    nested_dict_spec.specs["dict"].spec.dict_spec.CopyFrom(dict_spec)
    return nested_dict_spec


nested_dict_spec_good = nested_dict_spec(int_spec_inputs[0][0], double_spec_inputs[0][0],
                                         string_spec_inputs[0][0], bool_spec_inputs[0][0],
                                         roi_spec_inputs[0][0], list_spec_inputs[0][0],
                                         small_one_of_spec_good, small_dict_spec_good)

nested_dict_spec_bad = service_customization_pb2.DictParam.Spec()
nested_dict_spec_bad.CopyFrom(nested_dict_spec_good)
#Arbitrary bad sub-spec
nested_dict_spec_bad.specs["roi"].spec.roi_spec.CopyFrom(roi_spec_inputs[-1][0])


def nested_one_of_spec(nested_dict_spec, other_dict_spec, default_key="nested"):
    nested_one_of_spec = service_customization_pb2.OneOfParam.Spec()
    nested_one_of_spec.specs["nested"].spec.CopyFrom(nested_dict_spec)
    nested_one_of_spec.specs["simple"].spec.CopyFrom(other_dict_spec)
    nested_one_of_spec.default_key = "nested"
    return nested_one_of_spec


nested_one_of_spec_good = nested_one_of_spec(nested_dict_spec_good, small_dict_spec_good)
nested_one_of_spec_bad = nested_one_of_spec(nested_dict_spec_bad, small_dict_spec_good)

dict_spec_inputs = [
    (small_dict_spec_good, _DictParamValidator, True),
    (nested_dict_spec_good, _DictParamValidator, True),
    (small_dict_spec_bad, _DictParamValidator, False),
    (nested_dict_spec_bad, _DictParamValidator, False)
] #yapf: disable

one_of_spec_inputs = [
    (small_one_of_spec_good, _OneOfParamValidator, True),
    (nested_one_of_spec_good, _OneOfParamValidator, True),
    (small_one_of_spec_no_key, _OneOfParamValidator, True),
    (small_one_of_spec_bad_dict, _OneOfParamValidator, False),
    (small_one_of_spec_bad_key, _OneOfParamValidator, False),
    (nested_one_of_spec_bad, _OneOfParamValidator, False)
] #yapf: disable

all_input_specs = (int_spec_inputs + double_spec_inputs + string_spec_inputs + bool_spec_inputs +
                   roi_spec_inputs + custom_spec_inputs + list_spec_inputs + dict_spec_inputs +
                   one_of_spec_inputs)


@pytest.mark.parametrize("spec,spec_helper,is_valid", all_input_specs)
def test_custom_parameter_spec(spec, spec_helper, is_valid):
    if is_valid:
        assert spec_helper(spec).validate_spec() is None
        if spec_helper is _DictParamValidator:
            assert validate_dict_spec(spec) is None
    else:
        with pytest.raises(InvalidCustomParamSpecError) as e_info:
            spec_helper(spec).validate_spec()
            assert isinstance(e_info.value, list)
            assert len(e_info.value) > 0
        if spec_helper is _DictParamValidator:
            with pytest.raises(InvalidCustomParamSpecError) as e_info:
                validate_dict_spec(spec)
                assert isinstance(e_info.value, list)
                assert len(e_info.value) > 0


# Test cases are built individually in an attempt to minimize number of test cases necessary for decent coverage
# Cases should be structured with passing cases first, and failing cases second for easier indexing of good vs. bad cases

# Value helper functions


def custom_value(type_string, original_value):
    custom_value = service_customization_pb2.CustomParam()
    value_string = type_string + "_value"
    getattr(custom_value, value_string).CopyFrom(original_value)
    return custom_value


int_value_inputs = [
    (service_customization_pb2.Int64Param(value=5), int_spec_inputs[0][0], _Int64ParamValidator, True),
    (service_customization_pb2.Int64Param(value=21341), int_spec_inputs[2][0], _Int64ParamValidator, True),
    (service_customization_pb2.Int64Param(value=-1), int_spec_inputs[0][0], _Int64ParamValidator, False),
    (service_customization_pb2.Int64Param(value=55), int_spec_inputs[0][0], _Int64ParamValidator, False)
] #yapf: disable

double_value_inputs = [
    (service_customization_pb2.DoubleParam(value=0.3183), double_spec_inputs[0][0], _DoubleParamValidator, True),
    (service_customization_pb2.DoubleParam(value=-67.234), double_spec_inputs[2][0], _DoubleParamValidator, True),
    (service_customization_pb2.DoubleParam(value=-50), double_spec_inputs[0][0], _DoubleParamValidator, False),
    (service_customization_pb2.DoubleParam(value=234223.2), double_spec_inputs[0][0], _DoubleParamValidator, False)
] #yapf: disable

string_value_inputs = [
    (service_customization_pb2.StringParam(value="blue"), string_spec_inputs[0][0], _StringParamValidator, True),
    (service_customization_pb2.StringParam(value="anything"), string_spec_inputs[1][0], _StringParamValidator, True),
    (service_customization_pb2.StringParam(value="notanoption"), string_spec_inputs[0][0], _StringParamValidator, False)
] #yapf: disable

bool_value_inputs = [
    (service_customization_pb2.BoolParam(value=True), bool_spec_inputs[0][0], _BoolParamValidator, True)
] #yapf: disable

good_roi_val = service_customization_pb2.RegionOfInterestParam(
    area=image_geometry_pb2.AreaI(
        rectangle=image_geometry_pb2.RectangleI(x=5, y=10, cols=10, rows=25)),
    service_and_source=make_roi_service_and_source('fakeservice',
                                                   'fakesource'), image_cols=400, image_rows=400)
bad_roi_val = service_customization_pb2.RegionOfInterestParam()
bad_roi_val.CopyFrom(good_roi_val)
bad_roi_val.image_cols = -1

roi_value_inputs = [
    (good_roi_val, roi_spec_inputs[0][0], _RegionOfInterestParamValidator, True),
    (bad_roi_val, roi_spec_inputs[0][0], _RegionOfInterestParamValidator, False),
    (good_roi_val, roi_spec_inputs[1][0], _RegionOfInterestParamValidator, False),
] #yapf: disable

custom_value_inputs = [
    (custom_value("roi", good_roi_val), custom_spec("roi", roi_spec_inputs[0][0]), _CustomParamValidator, True),
    (custom_value("string", string_value_inputs[-1][0]), custom_spec("string", string_value_inputs[-1][1]), _CustomParamValidator, False)
] #yapf: disable

good_int_list_value = service_customization_pb2.ListParam()
good_int_list_value.values.append(custom_value("int", int_value_inputs[0][0]))
good_int_list_value.values.append(custom_value("int",
                                               service_customization_pb2.Int64Param(value=2)))

zero_size_list_value = service_customization_pb2.ListParam()

bad_int_list_value = service_customization_pb2.ListParam()
bad_int_list_value.CopyFrom(good_int_list_value)
bad_int_list_value.values.append(custom_value("int",
                                              service_customization_pb2.Int64Param(value=-5)))

bad_type_list_value = service_customization_pb2.ListParam()
bad_type_list_value.values.append(custom_value("roi", roi_value_inputs[0][0]))

list_value_inputs = [
    (good_int_list_value, list_spec_inputs[0][0], _ListParamValidator, True),
    (zero_size_list_value, list_spec_inputs[1][0], _ListParamValidator, True),
    (zero_size_list_value, list_spec_inputs[0][0], _ListParamValidator, False),
    (bad_int_list_value, list_spec_inputs[0][0], _ListParamValidator, False),
    (bad_type_list_value, list_spec_inputs[1][0], _ListParamValidator, False)
] #yapf: disable


#Uses keys from small_dict_spec above
def small_dict_value(int64value, stringvalue):
    dict_value = service_customization_pb2.DictParam()
    dict_value.values["int"].int_value.CopyFrom(int64value)
    dict_value.values["string_options"].string_value.CopyFrom(stringvalue)
    return dict_value


small_dict_value_good = small_dict_value(int_value_inputs[0][0], string_value_inputs[0][0])
small_dict_value_bad = small_dict_value(int_value_inputs[-1][0], string_value_inputs[0][0])


#Uses keys from small_one_of_spec above
def small_one_of_value(dict_value1, dict_value2, key="option 1"):
    one_of_value = service_customization_pb2.OneOfParam()
    one_of_value.values["option 1"].CopyFrom(dict_value1)
    one_of_value.values["option 2"].CopyFrom(dict_value2)
    one_of_value.key = key
    return one_of_value


small_one_of_value_good = small_one_of_value(small_dict_value_good, small_dict_value_good)
small_one_of_value_bad_key = small_one_of_value(small_dict_value_good, small_dict_value_good,
                                                key="notakey")
small_one_of_value_bad_dict = small_one_of_value(small_dict_value_good, small_dict_value_bad,
                                                 key="option 2")


#Uses keys from nested_dict_spec above
def nested_dict_value(int_value, double_value, string_value, bool_value, roi_value, list_value,
                      one_of_value, dict_value):
    nested_dict_value = service_customization_pb2.DictParam()
    nested_dict_value.values["int"].int_value.CopyFrom(int_value)
    nested_dict_value.values["double"].double_value.CopyFrom(double_value)
    nested_dict_value.values["string"].string_value.CopyFrom(string_value)
    nested_dict_value.values["bool"].bool_value.CopyFrom(bool_value)
    nested_dict_value.values["roi"].roi_value.CopyFrom(roi_value)
    nested_dict_value.values["list"].list_value.CopyFrom(list_value)
    nested_dict_value.values["one_of"].one_of_value.CopyFrom(one_of_value)
    nested_dict_value.values["dict"].dict_value.CopyFrom(dict_value)
    return nested_dict_value


nested_dict_value_good = nested_dict_value(int_value_inputs[0][0], double_value_inputs[0][0],
                                           string_value_inputs[0][0], bool_value_inputs[0][0],
                                           roi_value_inputs[0][0], list_value_inputs[0][0],
                                           small_one_of_value_good, small_dict_value_good)

nested_dict_value_bad = service_customization_pb2.DictParam()
nested_dict_value_bad.CopyFrom(nested_dict_value_good)
nested_dict_value_bad.values["list"].list_value.CopyFrom(bad_int_list_value)


#Uses keys from nested_one_of_spec above
def nested_one_of_value(nested_dict_value, other_dict_value, key="nested"):
    nested_one_of_value = service_customization_pb2.OneOfParam()
    nested_one_of_value.values["nested"].CopyFrom(nested_dict_value)
    nested_one_of_value.values["simple"].CopyFrom(other_dict_value)
    nested_one_of_value.key = key
    return nested_one_of_value


nested_one_of_value_good = nested_one_of_value(nested_dict_value_good, small_dict_value_good,
                                               key="simple")
nested_one_of_value_bad = nested_one_of_value(nested_dict_value_bad, small_dict_value_good)

dict_value_inputs = [
    (small_dict_value_good, small_dict_spec_good, _DictParamValidator, True),
    (nested_dict_value_good, nested_dict_spec_good, _DictParamValidator, True),
    (small_dict_value_bad, small_dict_spec_good, _DictParamValidator, False),
    (nested_dict_value_bad, nested_dict_spec_good, _DictParamValidator, False),
    (small_dict_value_good, nested_dict_spec_good, _DictParamValidator, False)
] #yapf: disable

one_of_value_inputs = [
    (small_one_of_value_good, small_one_of_spec_good, _OneOfParamValidator, True),
    (nested_one_of_value_good, nested_one_of_spec_good, _OneOfParamValidator, True),
    (small_one_of_value_bad_dict, small_one_of_spec_good, _OneOfParamValidator, False),
    (small_one_of_value_bad_key, small_one_of_spec_good, _OneOfParamValidator, False),
    (nested_one_of_value_bad, nested_one_of_spec_good, _OneOfParamValidator, False),
    (nested_one_of_value_good, small_one_of_spec_good, _OneOfParamValidator, False)
] #yapf: disable

all_input_values = (int_value_inputs + double_value_inputs + string_value_inputs +
                    bool_value_inputs + roi_value_inputs + custom_value_inputs + list_value_inputs +
                    dict_value_inputs + one_of_value_inputs)


@pytest.mark.parametrize("value,spec,spec_helper,is_valid", all_input_values)
def test_custom_parameter_values(value, spec, spec_helper, is_valid):
    error_proto = spec_helper(spec).validate_value(value)
    dict_validator_result = None
    if spec_helper is _DictParamValidator:
        dict_validator = create_value_validator(spec)
        dict_validator_result = dict_validator(value)
    if is_valid:
        assert error_proto is None
    else:
        assert type(error_proto) is service_customization_pb2.CustomParamError
        assert error_proto.status is not service_customization_pb2.CustomParamError.STATUS_OK
        assert len(error_proto.error_messages) > 0
    if spec_helper is _DictParamValidator:
        assert error_proto == dict_validator_result


int_value_inputs_for_coercion = [
    (service_customization_pb2.Int64Param(value=5), int_spec_inputs[0][0], int_param_coerce_to, service_customization_pb2.Int64Param(value=5), False),  # no coercion pos value
    (service_customization_pb2.Int64Param(value=21341), int_spec_inputs[2][0], int_param_coerce_to, service_customization_pb2.Int64Param(value=21341), False),  # no coercion pos value, no max
    (service_customization_pb2.Int64Param(value=-21341), int_spec_inputs[1][0], int_param_coerce_to, service_customization_pb2.Int64Param(value=-21341), False),  # no coercion neg value, no min
    (service_customization_pb2.Int64Param(value=-1), int_spec_inputs[0][0], int_param_coerce_to, service_customization_pb2.Int64Param(value=3), True),  # coercion neg value, param below min
    (service_customization_pb2.Int64Param(value=55), int_spec_inputs[0][0], int_param_coerce_to, service_customization_pb2.Int64Param(value=3), True),  # coercion pos value, param above max
    (service_customization_pb2.Int64Param(value=9), int_spec_inputs[0][0], int_param_coerce_to, service_customization_pb2.Int64Param(value=9), False),  # setting param to spec max
    (service_customization_pb2.Int64Param(value=1), int_spec_inputs[0][0], int_param_coerce_to, service_customization_pb2.Int64Param(value=1), False),  # setting param to spec min
    (service_customization_pb2.Int64Param(value=None), int_spec_inputs[2][0], int_param_coerce_to, service_customization_pb2.Int64Param(value=None), False),
    (service_customization_pb2.Int64Param(value=5), make_int64_param_spec(min_value=6, max_value=8), int_param_coerce_to, service_customization_pb2.Int64Param(value=6), True),  # coercion: value is smaller than min
    (service_customization_pb2.Int64Param(value=10), make_int64_param_spec(min_value=6, max_value=8), int_param_coerce_to, service_customization_pb2.Int64Param(value=6), True)  # coercion: value is larger than max
] #yapf: disable

double_value_inputs_for_coercion = [
    (service_customization_pb2.DoubleParam(value=0.3183), double_spec_inputs[0][0], double_param_coerce_to, service_customization_pb2.DoubleParam(value=0.3183), False),  # no coercion pos value
    (service_customization_pb2.DoubleParam(value=-67.234), double_spec_inputs[1][0], double_param_coerce_to, service_customization_pb2.DoubleParam(value=-67.234), False),  # no coercion pos value, no min
    (service_customization_pb2.DoubleParam(value=564267.234), double_spec_inputs[2][0], double_param_coerce_to, service_customization_pb2.DoubleParam(value=564267.234), False),  # no coercion pos value, no max
    (service_customization_pb2.DoubleParam(value=-50), double_spec_inputs[0][0], double_param_coerce_to, service_customization_pb2.DoubleParam(value=0.01), True),  # coercion pos value, param below min
    (service_customization_pb2.DoubleParam(value=234223.2), double_spec_inputs[0][0], double_param_coerce_to, service_customization_pb2.DoubleParam(value=0.01), True),  # coercion pos value, param above max
    (service_customization_pb2.DoubleParam(value=0.0), double_spec_inputs[0][0], double_param_coerce_to, service_customization_pb2.DoubleParam(value=0.0), False),  # no coercion, using zero
    (service_customization_pb2.DoubleParam(value=None), double_spec_inputs[2][0], double_param_coerce_to, service_customization_pb2.DoubleParam(value=None), False),
    (service_customization_pb2.DoubleParam(value=5.5), make_double_param_spec(min_value=5.9, max_value=8.7), double_param_coerce_to, service_customization_pb2.DoubleParam(value=5.9), True),  # coercion: value is smaller than min
    (service_customization_pb2.DoubleParam(value=10.9), make_double_param_spec(min_value=5.9, max_value=8.7), double_param_coerce_to, service_customization_pb2.DoubleParam(value=5.9), True)  # coercion: value is larger than max

] #yapf: disable

string_value_inputs_for_coercion = [
    (service_customization_pb2.StringParam(value="blue"), string_spec_inputs[0][0], string_param_coerce_to, service_customization_pb2.StringParam(value="blue"), False),  # not editable, blue is an option
    (service_customization_pb2.StringParam(value="notanoption"), string_spec_inputs[0][0], string_param_coerce_to, service_customization_pb2.StringParam(value="red"), True),  # not editable, param val is not an option
    (service_customization_pb2.StringParam(value="anything"), string_spec_inputs[1][0], string_param_coerce_to, service_customization_pb2.StringParam(value="anything"), False),  # not editable but no options given
    (service_customization_pb2.StringParam(value="anything"), string_spec_inputs[2][0], string_param_coerce_to, service_customization_pb2.StringParam(value="anything"), False),  # editable, any val is valid
    (service_customization_pb2.StringParam(value=None), string_spec_inputs[3][0], string_param_coerce_to, service_customization_pb2.StringParam(value=None), False)
] #yapf: disable


def build_list_for_coercion_tests(list_type, list_value, size):
    test_list = service_customization_pb2.ListParam()
    for x in range(size):
        test_list.values.append(custom_value(list_type, list_value))
    return test_list


coerced_int_list0 = build_list_for_coercion_tests("int",
                                                  service_customization_pb2.Int64Param(value=5), 1)
coerced_int_list0.values.append(custom_value("int", service_customization_pb2.Int64Param(value=2)))
coerced_int_list1 = build_list_for_coercion_tests("int", int_value_inputs[0][0], 1)
coerced_int_list1.values.append(custom_value("int", service_customization_pb2.Int64Param(value=2)))
coerced_int_list1.values.append(custom_value("int", service_customization_pb2.Int64Param(value=3)))
coerced_int_list2 = build_list_for_coercion_tests("int",
                                                  service_customization_pb2.Int64Param(value=3), 5)
coerced_int_list3 = build_list_for_coercion_tests("int",
                                                  service_customization_pb2.Int64Param(value=3), 4)
coerced_int_list4 = build_list_for_coercion_tests("int",
                                                  service_customization_pb2.Int64Param(value=3), 1)

coerced_int_list5 = build_list_for_coercion_tests("int",
                                                  service_customization_pb2.Int64Param(value=3), 1)

coerced_string_list1 = service_customization_pb2.ListParam()

good_int_list_value_for_coercion = copy.deepcopy(good_int_list_value)
bad_int_list_value_for_coercion = copy.deepcopy(bad_int_list_value)
zero_size_list_value_for_coercion = copy.deepcopy(zero_size_list_value)

list_value_inputs_for_coercion = [
    (good_int_list_value_for_coercion, list_spec_inputs[0][0], list_param_coerce_to, coerced_int_list0, False),  # int list no coercion , good list = [5, 2]
    (bad_int_list_value_for_coercion, list_spec_inputs[0][0], list_param_coerce_to, coerced_int_list1, True),  # int list coercion , bad list [5, 2, -5],
    (coerced_int_list2, list_spec_inputs[0][0], list_param_coerce_to, coerced_int_list3, True),  # int list coercion, param len is greater than max num of values
    (zero_size_list_value_for_coercion, list_spec_inputs[1][0], list_param_coerce_to, coerced_string_list1, False),  # list of strings, no min, should be valid
    (zero_size_list_value_for_coercion, list_spec_inputs[0][0], list_param_coerce_to, coerced_int_list4, True),  # list of ints, min size is 1, not valid setting param to contain spec default value
] #yapf: disable

small_dict_value_good_expected = small_dict_value(
    service_customization_pb2.Int64Param(value=5),
    service_customization_pb2.StringParam(value="blue"))
small_dict_value_bad_expected = small_dict_value(
    service_customization_pb2.Int64Param(value=3),
    service_customization_pb2.StringParam(value="blue"))
small_dict_value_bad_expected1 = small_dict_value(
    service_customization_pb2.Int64Param(value=3),
    service_customization_pb2.StringParam(value="red"))

small_one_of_value_good_expected = small_one_of_value(small_dict_value_good, small_dict_value_good)
small_one_of_value_bad_expected = small_one_of_value(small_dict_value_bad_expected,
                                                     small_dict_value_bad_expected)

small_one_of_value_bad_expected1 = small_one_of_value(small_dict_value_bad_expected1,
                                                      small_dict_value_bad_expected1)
good_roi_val_expected = service_customization_pb2.RegionOfInterestParam(
    area=image_geometry_pb2.AreaI(
        rectangle=image_geometry_pb2.RectangleI(x=5, y=10, cols=10, rows=25)),
    service_and_source=make_roi_service_and_source('fakeservice',
                                                   'fakesource'), image_cols=400, image_rows=400)

bad_roi_val_expected = service_customization_pb2.RegionOfInterestParam(
    area=image_geometry_pb2.AreaI(rectangle=image_geometry_pb2.RectangleI(x=10, cols=5, rows=10)),
    service_and_source=make_roi_service_and_source('fake_service',
                                                   'fake_source'), image_cols=0, image_rows=0)

nested_dict_value_good_expected = nested_dict_value(
    service_customization_pb2.Int64Param(value=5),
    service_customization_pb2.DoubleParam(value=0.3183),
    service_customization_pb2.StringParam(value="blue"),
    service_customization_pb2.BoolParam(value=True), good_roi_val_expected, coerced_int_list0,
    small_one_of_value_good_expected, small_dict_value_good_expected)

nested_dict_value_bad_expected = service_customization_pb2.DictParam()
nested_dict_value_bad_expected.CopyFrom(nested_dict_value_good_expected)
nested_dict_value_bad_expected.values["list"].list_value.CopyFrom(coerced_int_list1)

nested_one_of_value_good_expected = nested_one_of_value(nested_dict_value_good_expected,
                                                        small_dict_value_good_expected,
                                                        key="simple")
nested_one_of_value_bad_expected = nested_one_of_value(nested_dict_value_bad_expected,
                                                       small_dict_value_good_expected)

small_one_of_value_bad_key_expected = small_one_of_value(small_dict_value_good_expected,
                                                         small_dict_value_good_expected,
                                                         key="option 1")
small_one_of_value_bad_dict_expected = small_one_of_value(small_dict_value_good_expected,
                                                          small_dict_value_bad_expected,
                                                          key="option 2")

nested_dict_value_good_expected1 = nested_dict_value(
    service_customization_pb2.Int64Param(value=5),
    service_customization_pb2.DoubleParam(value=0.01),
    service_customization_pb2.StringParam(value='red'),
    service_customization_pb2.BoolParam(value=True), bad_roi_val_expected, coerced_int_list5,
    small_one_of_value_bad_expected1, small_dict_value_bad_expected1)

small_dict_value_good_for_coercion = copy.deepcopy(small_dict_value_good)
nested_dict_value_good_for_coercion = copy.deepcopy(nested_dict_value_good)
small_dict_value_bad_for_coercion = copy.deepcopy(small_dict_value_bad)
nested_dict_value_bad_for_coercion = copy.deepcopy(nested_dict_value_bad)

dict_value_inputs_for_coercion = [
    (small_dict_value_good_for_coercion, small_dict_spec_good, dict_param_coerce_to, small_dict_value_good_expected, False),  # no coercion
    (nested_dict_value_good_for_coercion, nested_dict_spec_good, dict_param_coerce_to, nested_dict_value_good_expected, False),  # nested dict, no coercion
    (small_dict_value_bad_for_coercion, small_dict_spec_good, dict_param_coerce_to, small_dict_value_bad_expected, True),  # coercion, invalid int, valid string
    (nested_dict_value_bad_for_coercion, nested_dict_spec_good, dict_param_coerce_to, nested_dict_value_bad_expected, True),  # coercion, invalid int in list
    (small_dict_value_good_for_coercion, nested_dict_spec_good, dict_param_coerce_to, nested_dict_value_good_expected1, True)  # coercion, missing values in param
] #yapf: disable

small_one_of_value_good_for_coercion = copy.deepcopy(small_one_of_value_good)
nested_one_of_value_good_for_coercion = copy.deepcopy(nested_one_of_value_good)
small_one_of_value_bad_dict_for_coercion = copy.deepcopy(small_one_of_value_bad_dict)
small_one_of_value_bad_key_for_coercion = copy.deepcopy(small_one_of_value_bad_key)
nested_one_of_value_bad_for_coercion = copy.deepcopy(nested_one_of_value_bad)

one_of_value_inputs_for_coercion = [
    (small_one_of_value_good_for_coercion, small_one_of_spec_good, one_of_param_coerce_to, small_one_of_value_good_expected, False),  # no coercion
    (nested_one_of_value_good_for_coercion, nested_one_of_spec_good, one_of_param_coerce_to, nested_one_of_value_good_expected, False),  # no coercion
    (small_one_of_value_bad_dict_for_coercion, small_one_of_spec_good, one_of_param_coerce_to, small_one_of_value_bad_dict_expected, True),  # coercion, bad option 2 with invalid int
    (small_one_of_value_bad_key_for_coercion, small_one_of_spec_good, one_of_param_coerce_to, small_one_of_value_good_expected, True),  # coercion, invalid key
    (nested_one_of_value_bad_for_coercion, nested_one_of_spec_good, one_of_param_coerce_to, nested_one_of_value_bad_expected, True),  # coercion, invalid nested list
    (nested_one_of_value_good_for_coercion, small_one_of_spec_good, one_of_param_coerce_to, small_one_of_value_bad_expected1, True)  # coercion, two invalid options, bad string and int values
] #yapf: disable

inputs_for_coercion = int_value_inputs_for_coercion + double_value_inputs_for_coercion + string_value_inputs_for_coercion + list_value_inputs_for_coercion + dict_value_inputs_for_coercion + one_of_value_inputs_for_coercion


@pytest.mark.parametrize("param,spec,spec_helper,expected,was_coerced", inputs_for_coercion)
def test_parameter_coercion(param, spec, spec_helper, expected, was_coerced):
    assert spec_helper(param, spec) == was_coerced
    assert param == expected


def _check_dict(dict_values, dict_param):
    for key, value in dict_values.items():
        custom_param = dict_param.values[key]
        value_field = custom_param.WhichOneof("value")
        param_value = getattr(custom_param, value_field)

        if type(param_value) is service_customization_pb2.OneOfParam:
            _check_dict(value, param_value.values[param_value.key])
        elif type(value) is dict:
            _check_dict(value, param_value)
        elif type(value) is list:
            _check_list(value, param_value)
        elif type(value) is service_customization_pb2.RegionOfInterestParam:
            assert value == param_value
        else:
            assert value == param_value.value


def _check_list(list_values, list_param):
    assert len(list_values) == len(list_param.values)
    for ind, value in enumerate(list_values):
        custom_param = list_param.values[ind]
        value_field = custom_param.WhichOneof("value")
        param_value = getattr(custom_param, value_field)

        if type(param_value) is service_customization_pb2.OneOfParam:
            _check_dict(value, param_value.values[param_value.key])
        elif type(value) is dict:
            _check_dict(value, param_value)
        elif type(value) is list:
            _check_list(value, param_value)
        elif type(value) is service_customization_pb2.RegionOfInterestParam:
            assert value == param_value
        else:
            assert value == param_value.value


@pytest.mark.parametrize("value,spec,spec_helper,is_valid", dict_value_inputs)
def test_dict_params_to_dict(value, spec, spec_helper, is_valid):
    if is_valid:
        dict_values = dict_params_to_dict(value, spec)
        _check_dict(dict_values, value)
    else:
        raised_error = False
        try:
            dict_values = dict_params_to_dict(value, spec)
            _check_dict(dict_values, value)
        except:
            raised_error = True

        assert raised_error


@pytest.mark.parametrize("value,spec,spec_helper,is_valid", list_value_inputs)
def test_list_params_to_list(value, spec, spec_helper, is_valid):
    if is_valid:
        list_values = list_params_to_list(value, spec)
        _check_list(list_values, value)
    else:
        raised_error = False
        try:
            list_values = list_params_to_list(value, spec)
        except:
            raised_error = True

        assert raised_error


@pytest.mark.parametrize("value,spec,spec_helper,is_valid", one_of_value_inputs)
def test_oneof_param_to_dict(value, spec, spec_helper, is_valid):
    if is_valid:
        dict_values = oneof_param_to_dict(value, spec)
        _check_dict(dict_values, value.values[value.key])
    else:
        raised_error = False
        try:
            dict_values = oneof_param_to_dict(value, spec)
        except:
            raised_error = True

        assert raised_error


# explicitly test spec creator helper functions
int_64_param_specs = [
    (make_int64_param_spec(3, units_pb2.Units(name='feet'), 2, 6),
     service_customization_pb2.Int64Param.Spec(default_value=wrappers.Int64Value(value=3),
                                               units=units_pb2.Units(name='feet'),
                                               min_value=wrappers.Int64Value(value=2),
                                               max_value=wrappers.Int64Value(value=6)), True),
    (make_int64_param_spec(-4, units_pb2.Units(name='cm')),
     service_customization_pb2.Int64Param.Spec(default_value=wrappers.Int64Value(value=-4),
                                               units=units_pb2.Units(name='cm')), True),
    (make_int64_param_spec(-4, units_pb2.Units(name='cm')),
     service_customization_pb2.Int64Param.Spec(default_value=wrappers.Int64Value(value=-5),
                                               units=units_pb2.Units(name='cm')), False)
]

double_param_specs = [
    (make_double_param_spec(3.6, units_pb2.Units(name='inches'), 2.2, 6.7),
     service_customization_pb2.DoubleParam.Spec(default_value=wrappers.DoubleValue(value=3.6),
                                                units=units_pb2.Units(name='inches'),
                                                min_value=wrappers.DoubleValue(value=2.2),
                                                max_value=wrappers.DoubleValue(value=6.7)), True),
    (make_double_param_spec(-4.5, units_pb2.Units(name='mL')),
     service_customization_pb2.DoubleParam.Spec(default_value=wrappers.DoubleValue(value=-4.5),
                                                units=units_pb2.Units(name='mL')), True),
    (make_double_param_spec(-4.5, units_pb2.Units(name='mL')),
     service_customization_pb2.DoubleParam.Spec(default_value=wrappers.DoubleValue(value=-5.5),
                                                units=units_pb2.Units(name='mL')), False)
]

string_param_specs = [
    (make_string_param_spec(default_value='hello world'),
     service_customization_pb2.StringParam.Spec(default_value='hello world'), True),
    (make_string_param_spec(options=[], default_value='hello world'),
     service_customization_pb2.StringParam.Spec(default_value='hello world'), True),
    (make_string_param_spec(default_value='hello world'),
     service_customization_pb2.StringParam.Spec(options=None, default_value='hello world'), True),
    (make_string_param_spec(options=['abc', 'def'], editable=True, default_value='abc'),
     service_customization_pb2.StringParam.Spec(options=['abc', 'def'], editable=True,
                                                default_value='abc'), True),
    (make_string_param_spec(options=['abc', 'def'], editable=True, default_value='abc'),
     service_customization_pb2.StringParam.Spec(options=['abc', 'def'], editable=False,
                                                default_value='def'), False),
    (make_string_param_spec(options=['abc', 'def'], editable=False, default_value='abc'),
     service_customization_pb2.StringParam.Spec(options=['abc', 'def'], editable=False,
                                                default_value='def'), False)
]

bool_param_specs = [
    (make_bool_param_spec(default_value=True),
     service_customization_pb2.BoolParam.Spec(default_value=wrappers.BoolValue(value=True)), True),
    (make_bool_param_spec(default_value=True),
     service_customization_pb2.BoolParam.Spec(default_value=wrappers.BoolValue(value=False)),
     False),
    (make_bool_param_spec(default_value=None), service_customization_pb2.BoolParam.Spec(), True),
    (make_bool_param_spec(), service_customization_pb2.BoolParam.Spec(), True)
]

roi_param_specs = [
    (make_region_of_interest_param_spec(
        make_roi_service_and_source('fakeservice', 'fakesource'),
        image_geometry_pb2.AreaI(
            rectangle=image_geometry_pb2.RectangleI(x=5, y=10, cols=10, rows=25)), True),
     service_customization_pb2.RegionOfInterestParam.Spec(
         service_and_source=service_customization_pb2.RegionOfInterestParam.ServiceAndSource(
             service='fakeservice', source='fakesource'), default_area=image_geometry_pb2.AreaI(
                 rectangle=image_geometry_pb2.RectangleI(x=5, y=10, cols=10, rows=25)),
         allows_rectangle=True), True),
    (make_region_of_interest_param_spec(make_roi_service_and_source('fakeservice', 'fakesource')),
     service_customization_pb2.RegionOfInterestParam.Spec(
         service_and_source=service_customization_pb2.RegionOfInterestParam.ServiceAndSource(
             service='fakeservice', source='fakesource')), True),
    (make_region_of_interest_param_spec(
        make_roi_service_and_source('fakeservice', 'fakesource'),
        image_geometry_pb2.AreaI(
            rectangle=image_geometry_pb2.RectangleI(x=5, y=10, cols=15, rows=25)), True),
     service_customization_pb2.RegionOfInterestParam.Spec(
         service_and_source=service_customization_pb2.RegionOfInterestParam.ServiceAndSource(
             service='fakeservice', source='fakesource'), default_area=image_geometry_pb2.AreaI(
                 rectangle=image_geometry_pb2.RectangleI(x=5, y=10, cols=10, rows=25)),
         allows_rectangle=True), False),
    (make_region_of_interest_param_spec(
        make_roi_service_and_source('fakeservice', 'fake_source'),
        image_geometry_pb2.AreaI(
            rectangle=image_geometry_pb2.RectangleI(x=5, y=10, cols=10, rows=25)), True),
     service_customization_pb2.RegionOfInterestParam.Spec(
         service_and_source=service_customization_pb2.RegionOfInterestParam.ServiceAndSource(
             service='fakeservice', source='fakesource'), default_area=image_geometry_pb2.AreaI(
                 rectangle=image_geometry_pb2.RectangleI(x=5, y=10, cols=10, rows=25)),
         allows_rectangle=True), False),
    (make_region_of_interest_param_spec(
        make_roi_service_and_source('fakeservice', 'fakesource'),
        image_geometry_pb2.AreaI(
            rectangle=image_geometry_pb2.RectangleI(x=5, y=10, cols=10, rows=25)), False),
     service_customization_pb2.RegionOfInterestParam.Spec(
         service_and_source=service_customization_pb2.RegionOfInterestParam.ServiceAndSource(
             service='fakeservice', source='fakesource'), default_area=image_geometry_pb2.AreaI(
                 rectangle=image_geometry_pb2.RectangleI(x=5, y=10, cols=10, rows=25)),
         allows_rectangle=True), False),
]

list_param_specs = [
    (make_list_param_spec(element_spec=make_custom_param_spec(spec=int_64_param_specs[0][0]),
                          min_number_of_values=1, max_number_of_values=2),
     service_customization_pb2.ListParam.Spec(
         element_spec=service_customization_pb2.CustomParam.Spec(int_spec=int_64_param_specs[0][0]),
         min_number_of_values=wrappers.Int64Value(value=1),
         max_number_of_values=wrappers.Int64Value(value=2)), True),
    (make_list_param_spec(element_spec=make_custom_param_spec(spec=int_64_param_specs[0][0]),
                          max_number_of_values=2),
     service_customization_pb2.ListParam.Spec(
         element_spec=service_customization_pb2.CustomParam.Spec(int_spec=int_64_param_specs[0][0]),
         max_number_of_values=wrappers.Int64Value(value=2)), True),
    (make_list_param_spec(element_spec=make_custom_param_spec(spec=int_64_param_specs[0][0]),
                          min_number_of_values=1),
     service_customization_pb2.ListParam.Spec(
         element_spec=service_customization_pb2.CustomParam.Spec(int_spec=int_64_param_specs[0][0]),
         min_number_of_values=wrappers.Int64Value(value=1)), True),
    (make_list_param_spec(element_spec=make_custom_param_spec(spec=int_64_param_specs[0][0]),
                          min_number_of_values=1, max_number_of_values=2),
     service_customization_pb2.ListParam.Spec(
         element_spec=service_customization_pb2.CustomParam.Spec(int_spec=int_64_param_specs[0][0]),
         min_number_of_values=wrappers.Int64Value(value=1),
         max_number_of_values=wrappers.Int64Value(value=3)), False),
    (make_list_param_spec(element_spec=make_custom_param_spec(spec=int_64_param_specs[0][0]),
                          min_number_of_values=1, max_number_of_values=2),
     service_customization_pb2.ListParam.Spec(
         element_spec=service_customization_pb2.CustomParam.Spec(int_spec=int_64_param_specs[0][0]),
         min_number_of_values=wrappers.Int64Value(value=0),
         max_number_of_values=wrappers.Int64Value(value=2)), False),
    (make_list_param_spec(element_spec=make_custom_param_spec(spec=int_64_param_specs[0][0]),
                          min_number_of_values=1, max_number_of_values=2),
     service_customization_pb2.ListParam.Spec(
         element_spec=service_customization_pb2.CustomParam.Spec(int_spec=int_64_param_specs[1][0]),
         min_number_of_values=wrappers.Int64Value(value=0),
         max_number_of_values=wrappers.Int64Value(value=2)), False),
]

dict_child_specs = [
    (make_dict_child_spec(param_spec=int_64_param_specs[0][0],
                          ui_info=make_user_interface_info(display_name='Feet')),
     service_customization_pb2.DictParam.ChildSpec(
         spec=service_customization_pb2.CustomParam.Spec(int_spec=int_64_param_specs[0][0]),
         ui_info=service_customization_pb2.UserInterfaceInfo(display_name='Feet')), True),
    (make_dict_child_spec(param_spec=string_param_specs[0][0],
                          ui_info=make_user_interface_info(display_name='Max Length')),
     service_customization_pb2.DictParam.ChildSpec(
         spec=service_customization_pb2.CustomParam.Spec(string_spec=string_param_specs[0][0]),
         ui_info=service_customization_pb2.UserInterfaceInfo(display_name='Max Length')), True),
    (make_dict_child_spec(param_spec=int_64_param_specs[0][0],
                          ui_info=make_user_interface_info(display_name='Feet')),
     service_customization_pb2.DictParam.ChildSpec(
         spec=service_customization_pb2.CustomParam.Spec(int_spec=int_64_param_specs[0][0]),
         ui_info=service_customization_pb2.UserInterfaceInfo(display_name='Inches')), False),
    (make_dict_child_spec(
        param_spec=int_64_param_specs[0][0],
        ui_info=make_user_interface_info(display_name='Feet', description='Distance',
                                         display_order=2)),
     service_customization_pb2.DictParam.ChildSpec(
         spec=service_customization_pb2.CustomParam.Spec(int_spec=int_64_param_specs[0][0]),
         ui_info=service_customization_pb2.UserInterfaceInfo(display_name='Feet',
                                                             description='Distance',
                                                             display_order=3)), False),
    (make_dict_child_spec(
        param_spec=int_64_param_specs[0][0],
        ui_info=make_user_interface_info(display_name='Feet', description='Distance',
                                         display_order=2)),
     service_customization_pb2.DictParam.ChildSpec(
         spec=service_customization_pb2.CustomParam.Spec(int_spec=int_64_param_specs[0][0]),
         ui_info=service_customization_pb2.UserInterfaceInfo(display_name='Feet',
                                                             description='Space',
                                                             display_order=2)), False),
    (make_dict_child_spec(
        param_spec=int_64_param_specs[0][0],
        ui_info=make_user_interface_info(display_name='Feet', description='Distance',
                                         display_order=2)),
     service_customization_pb2.DictParam.ChildSpec(
         spec=service_customization_pb2.CustomParam.Spec(int_spec=int_64_param_specs[0][0]),
         ui_info=service_customization_pb2.UserInterfaceInfo(display_name='Inches',
                                                             description='Distance',
                                                             display_order=2)), False)
]

dict_param_specs = [
    (make_dict_param_spec({
        'int': dict_child_specs[0][0],
        'string': dict_child_specs[1][0]
    }, is_hidden_by_default=False),
     service_customization_pb2.DictParam.Spec(
         specs={
             'int': dict_child_specs[0][0],
             'string': dict_child_specs[1][0]
         }, is_hidden_by_default=False), True),
    (make_dict_param_spec({
        'int': dict_child_specs[0][0],
        'string': dict_child_specs[1][0]
    }, is_hidden_by_default=False),
     service_customization_pb2.DictParam.Spec(
         specs={
             'int': dict_child_specs[1][0],
             'string': dict_child_specs[1][0]
         }, is_hidden_by_default=False), False),
    (make_dict_param_spec({
        'int': dict_child_specs[0][0],
        'string': dict_child_specs[1][0]
    }, is_hidden_by_default=False),
     service_customization_pb2.DictParam.Spec(
         specs={
             'int': dict_child_specs[0][0],
             'string': dict_child_specs[1][0]
         }, is_hidden_by_default=True), False)
]

one_of_child_specs = [
    (make_one_of_child_spec(dict_param_specs[0][0],
                            make_user_interface_info(display_name='Length')),
     service_customization_pb2.OneOfParam.ChildSpec(
         spec=dict_param_specs[0][0],
         ui_info=service_customization_pb2.UserInterfaceInfo(display_name='Length')), True),
    (make_one_of_child_spec(dict_param_specs[0][0],
                            make_user_interface_info(display_name='Length')),
     service_customization_pb2.OneOfParam.ChildSpec(
         spec=dict_param_specs[1][1],
         ui_info=service_customization_pb2.UserInterfaceInfo(display_name='Length')), False),
    (make_one_of_child_spec(dict_param_specs[0][0],
                            make_user_interface_info(display_name='Length')),
     service_customization_pb2.OneOfParam.ChildSpec(
         spec=dict_param_specs[0][0],
         ui_info=service_customization_pb2.UserInterfaceInfo(display_name='Max Length')), False),
    (make_one_of_child_spec(dict_param_specs[0][0]),
     service_customization_pb2.OneOfParam.ChildSpec(spec=dict_param_specs[0][0]), True)
]

one_of_param_specs = [
    (make_one_of_param_spec({
        'int': one_of_child_specs[0][0],
        'string': one_of_child_specs[1][0]
    }, default_key='int'),
     service_customization_pb2.OneOfParam.Spec(
         specs={
             'int': one_of_child_specs[0][0],
             'string': one_of_child_specs[1][0]
         }, default_key='int'), True),
    (make_one_of_param_spec({
        'int': one_of_child_specs[0][0],
        'string': one_of_child_specs[1][0]
    }, default_key='int'),
     service_customization_pb2.OneOfParam.Spec(
         specs={
             'int': one_of_child_specs[0][0],
             'string': one_of_child_specs[1][1]
         }, default_key='int'), False),
    (make_one_of_param_spec({
        'int': one_of_child_specs[0][0],
        'string': one_of_child_specs[1][0]
    }, default_key='int'),
     service_customization_pb2.OneOfParam.Spec(
         specs={
             'int': one_of_child_specs[0][0],
             'string': one_of_child_specs[1][0]
         }, default_key='string'), False)
]

param_spec_helpers = (int_64_param_specs + double_param_specs + string_param_specs +
                      bool_param_specs + roi_param_specs + list_param_specs + dict_child_specs +
                      dict_param_specs + one_of_child_specs + one_of_param_specs)


@pytest.mark.parametrize("generated,expected,is_valid", param_spec_helpers)
def test_param_spec_helpers(generated, expected, is_valid):
    assert (generated == expected) == is_valid
