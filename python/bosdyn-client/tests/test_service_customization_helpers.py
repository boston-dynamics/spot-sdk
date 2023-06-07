# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import pytest
from google.protobuf import wrappers_pb2 as wrappers

from bosdyn.api import image_geometry_pb2, service_customization_pb2
from bosdyn.client.service_customization_helpers import (InvalidCustomParamSpecError,
                                                         _BoolParamValidator, _CustomParamValidator,
                                                         _DictParamValidator, _DoubleParamValidator,
                                                         _Int64ParamValidator, _ListParamValidator,
                                                         _OneOfParamValidator,
                                                         _RegionOfInterestParamValidator,
                                                         _StringParamValidator,
                                                         create_value_validator, validate_dict_spec)

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


def string_spec(default_value=None, options=None):
    string_spec = service_customization_pb2.StringParam.Spec()
    if default_value is not None:
        string_spec.default_value = default_value
    if options is not None:
        string_spec.options.extend(options)
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
    ("red", ["red", "blue", "green"], True),
    ("default", None, True),
    (None, None, True),
    ("car", ["red"], False)
] #yapf: disable
string_spec_inputs = [(string_spec(*inputs[0:2]), _StringParamValidator, inputs[-1])
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

all_input_specs = int_spec_inputs + double_spec_inputs + string_spec_inputs + bool_spec_inputs + roi_spec_inputs + custom_spec_inputs + list_spec_inputs + dict_spec_inputs + one_of_spec_inputs


@pytest.mark.parametrize("spec,spec_helper,is_valid", all_input_specs)
def test_custom_parameter_spec(spec, spec_helper, is_valid):
    if is_valid:
        assert spec_helper(spec).validate_spec() is None
        if spec_helper is _DictParamValidator:
            assert validate_dict_spec(spec) is None
    else:
        with pytest.raises(InvalidCustomParamSpecError) as e_info:
            spec_helper(spec).validate_spec()
            assert type(e_info.value) == list
            assert len(e_info.value) > 0
        if spec_helper is _DictParamValidator:
            with pytest.raises(InvalidCustomParamSpecError) as e_info:
                validate_dict_spec(spec)
                assert type(e_info.value) == list
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
    service_and_source=service_customization_pb2.RegionOfInterestParam.ServiceAndSource(
        service="fakeservice", source="fakesource"), image_cols=400, image_rows=400)
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
    nested_one_of_value.key = "nested"
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

all_input_values = int_value_inputs + double_value_inputs + string_value_inputs + bool_value_inputs + roi_value_inputs + custom_value_inputs + list_value_inputs + dict_value_inputs + one_of_value_inputs


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
