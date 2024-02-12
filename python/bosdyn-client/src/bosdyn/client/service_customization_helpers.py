# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Union

from bosdyn.api.image_geometry_pb2 import AreaI
from bosdyn.api.service_customization_pb2 import (BoolParam, CustomParam, CustomParamError,
                                                  DictParam, DoubleParam, Int64Param, ListParam,
                                                  OneOfParam, RegionOfInterestParam, StringParam,
                                                  UserInterfaceInfo)
from bosdyn.api.units_pb2 import Units



class InvalidCustomParamSpecError(ValueError):
    """Error indicating that the defined custom parameter Spec is invalid,
    with a list of error messages explaining why the spec is invalid"""


class InvalidCustomParamValueError(ValueError):
    """Error indicating that the defined custom parameter value does not match
    the associated Spec, with a list of error messages explaining why."""

    def __init__(self, proto_error: CustomParamError):
        self.proto_error = proto_error


def validate_dict_spec(dict_spec: DictParam.Spec) -> None:
    """
    Checks that a DictParam.Spec is valid

    Args:
        dict_spec (service_customization_pb2.DictParam.Spec): Spec to be validated

    Returns:
        None for a valid spec

    Raises:
        InvalidCustomParamSpecError with a list of error messages for invalid specs.
    """
    return _DictParamValidator(dict_spec).validate_spec()


def create_value_validator(
        dict_spec: DictParam.Spec) -> Callable[[DictParam], Optional[CustomParamError]]:
    """
    Checks if the DictParam.Spec is value and if so, returns a function that can be used to validate any DictParam value

    Args:
        dict_spec (service_customization_pb2.DictParam.Spec): Spec to be validated and validate values against

    Raises:
        InvalidCustomParamSpecError with a list of error messages if the dict_spec is invalid

    Returns:
        A validate_value function that can be called on any value to verify it against this Spec.
        The returned function will itself return None if called on a valid value, and a CustomParamError
        with a status besides STATUS_OK for an invalid spec
    """
    validator = _DictParamValidator(dict_spec)

    # Raises an error if the Spec itself is invalid
    validator.validate_spec()

    return validator.validate_value


def dict_params_to_dict(dict_param: DictParam, dict_spec: DictParam.Spec,
                        validate: bool = True) -> Dict:
    if validate:
        validator = create_value_validator(dict_spec)
        validate_res = validator(dict_param)
        if validate_res:
            raise InvalidCustomParamValueError(validate_res)

    values = {}
    for (key, custom_param) in dict_param.values.items():
        value_field = custom_param.WhichOneof("value")
        spec_field = dict_spec.specs[key].spec.WhichOneof("spec")
        param_value = getattr(custom_param, value_field)
        param_spec = getattr(dict_spec.specs[key].spec, spec_field)

        if value_field == 'dict_value':
            values[key] = dict_params_to_dict(param_value, param_spec, validate=False)
        elif value_field == 'list_value':
            values[key] = list_params_to_list(param_value, param_spec, validate=False)
        elif value_field == 'one_of_value':
            values[key] = oneof_param_to_dict(param_value, param_spec, validate=False)
        elif value_field == 'roi_value':
            values[key] = param_value
        elif value_field in ['int_value', 'double_value', 'string_value', 'bool_value']:
            values[key] = param_value.value
        else:
            raise NotImplementedError(
                f'No handler for conversion of {value_field} from dict members.')

    return values


def list_params_to_list(list_param: ListParam, list_spec: ListParam.Spec,
                        validate: bool = True) -> List:
    if validate:
        validator = _ListParamValidator(list_spec)
        validator.validate_spec()
        validate_res = validator.validate_value(list_param)
        if validate_res:
            raise InvalidCustomParamValueError(validate_res)

    values = []
    for (ind, custom_param) in enumerate(list_param.values):
        value_field = custom_param.WhichOneof("value")
        spec_field = list_spec.element_spec.WhichOneof("spec")
        param_value = getattr(custom_param, value_field)
        param_spec = getattr(list_spec.element_spec, spec_field)

        if value_field == 'dict_value':
            values.append(dict_params_to_dict(param_value, param_spec, validate=False))
        elif value_field == 'list_value':
            values.append(list_params_to_list(param_value, param_spec, validate=False))
        elif value_field == 'one_of_value':
            values.append(oneof_param_to_dict(param_value, param_spec, validate=False))
        elif value_field == 'roi_value':
            values.append(param_value)
        elif value_field in ['int_value', 'double_value', 'string_value', 'bool_value']:
            values.append(param_value.value)
        else:
            raise NotImplementedError(
                f'No handler for conversion of {value_field} from list members.')

    return values


def oneof_param_to_dict(oneof_param: OneOfParam, oneof_spec: OneOfParam.Spec,
                        validate: bool = True) -> List:
    if validate:
        validator = _OneOfParamValidator(oneof_spec)
        validator.validate_spec()
        validate_res = validator.validate_value(oneof_param)
        if validate_res:
            raise InvalidCustomParamValueError(validate_res)

    dict_param = oneof_param.values[oneof_param.key]
    dict_spec = oneof_spec.specs[oneof_param.key].spec
    return dict_params_to_dict(dict_param, dict_spec)


def check_types_match(param, proto_type):
    if type(param) != proto_type:
        return CustomParamError(
            status=CustomParamError.STATUS_INVALID_VALUE,
            error_messages=[
                f"Param {param} has type {type(param)}" \
                f" but the spec requires {proto_type}."
            ])

    return None


class _ParamValidatorInterface(ABC):
    """ Class providing a common structure and interface to validate parameter types.

        Specifically, a <Type>ParamValidator class can be used to validate a service_customization_pb2.<Type>Param.Spec
        via a validate_spec function with a consistent signature, and can validate a service_customization_pb2.<Type>Param
        against a specific Spec via a validate_value function

        Args:
            param_spec (service_customization_pb2.<Type>Param.Spec): A Spec message for a type of custom parameter
    """

    @abstractmethod
    def __init__(self, param_spec):
        self.param_spec = param_spec

    @abstractmethod
    def validate_spec(self) -> None:
        """
        Checks if the parameter Spec is valid for its type

        Returns:
            None for a valid spec, and raises a CustomParamError with a status besides STATUS_OK for an invalid spec
        """
        pass

    @abstractmethod
    def validate_value(self, param_value) -> Optional[CustomParamError]:
        """
        Checks if a parameter value is valid for this class's self.param_spec

        Args:
            param_value (service_customization.<Type>Param): A custom parameter value to validate against self.param_spec

        Returns:
            None for a valid value, and returns a service_customization_pb2.CustomParamError with a status besides STATUS_OK for an invalid value
        """
        pass


class _DictParamValidator(_ParamValidatorInterface):
    """
    ParamValidator class for a service_customization_pb2.DictParam.Spec

    Args:
        param_spec (service_customization_pb2.DictParam.Spec): The DictParam Spec this helper instance is being used for
    """
    proto_type = DictParam
    custom_param_value_field = "dict_value"

    def __init__(self, param_spec):
        super().__init__(param_spec)

    def validate_spec(self):
        custom_param_error = CustomParamError(status=CustomParamError.STATUS_OK)
        error_list = []
        for name, child_spec in self.param_spec.specs.items():
            try:
                _CustomParamValidator(child_spec.spec).get_param_helper().validate_spec()
            except InvalidCustomParamSpecError as e:
                error_list.extend(_nested_error_message_helper(name, e.args[0]))
        if error_list:
            raise InvalidCustomParamSpecError(error_list)

    def validate_value(self, param_value):
        """
        Checks if a parameter value is valid for this class's self.param_spec

        Args:
            param_value (service_customization.DictParam): A custom parameter value to validate against self.param_spec

        Returns:
            Nothing for a valid spec, and raises a service_customization_pb2.CustomParamError for an invalid Spec.
        """
        err = check_types_match(param_value, self.proto_type)
        if err:
            return err

        value_keys = set(param_value.values.keys())
        spec_keys = set(self.param_spec.specs.keys())
        if not value_keys.issubset(spec_keys):
            return CustomParamError(
                status=CustomParamError.STATUS_UNSUPPORTED_PARAMETER, error_messages=[
                    f"DictParam value contains keys {value_keys - spec_keys} not present in the spec."
                ])
        custom_param_error = CustomParamError(status=CustomParamError.STATUS_OK)
        for name, custom_param in param_value.values.items():
            child_spec = self.param_spec.specs[name].spec
            child_value = getattr(custom_param, custom_param.WhichOneof("value"))
            error_proto = _CustomParamValidator(child_spec).get_param_helper().validate_value(
                child_value)
            if error_proto:
                custom_param_error.status = error_proto.status
                custom_param_error.error_messages.extend(
                    _nested_error_message_helper(name, error_proto.error_messages))
        if custom_param_error.status != CustomParamError.STATUS_OK:
            return custom_param_error


class _NumericalParamValidator(_ParamValidatorInterface):
    """
    Generic ParamValidator class for shared logic between numerical Param Specs

    Args:
        param_spec (service_customization_pb2.<Numerical>Param.Spec): The Numerical Spec this helper instance is being used for
    """

    def __init__(self, param_spec):
        super().__init__(param_spec)

    def validate_spec(self):
        error_messages = []
        if self.param_spec.HasField("min_value"):
            if self.param_spec.min_value.value > self.param_spec.default_value.value:
                error_messages.append("Default Spec Value below allowed minimum Value")
        if self.param_spec.HasField("max_value"):
            if self.param_spec.max_value.value < self.param_spec.default_value.value:
                error_messages.append("Default Spec Value above allowed maximum value")
        if self.param_spec.HasField("min_value") and self.param_spec.HasField("max_value"):
            if self.param_spec.min_value.value > self.param_spec.max_value.value:
                error_messages.append("min_value greater than max_value")
        if error_messages:
            raise InvalidCustomParamSpecError(error_messages)

    def validate_value(self, param_value):
        err = check_types_match(param_value, self.proto_type)
        if err:
            return err

        num_value = param_value.value
        if self.param_spec.HasField("min_value"):
            if num_value < self.param_spec.min_value.value:
                return CustomParamError(
                    status=CustomParamError.STATUS_INVALID_VALUE, error_messages=[
                        f"Value {num_value} below min_bound {self.param_spec.min_value.value}"
                    ])
        if self.param_spec.HasField("max_value"):
            if num_value > self.param_spec.max_value.value:
                return CustomParamError(
                    status=CustomParamError.STATUS_INVALID_VALUE, error_messages=[
                        f"Value {num_value} above max_bound {self.param_spec.max_value.value}"
                    ])


class _Int64ParamValidator(_NumericalParamValidator):
    """
    ParamValidator class for a service_customization_pb2.Int64Param.Spec

    Args:
        param_spec (service_customization_pb2.Int64Param.Spec): The Int64Param Spec this helper instance is being used for
    """

    proto_type = Int64Param
    custom_param_value_field = "int_value"

    def __init__(self, param_spec):
        super().__init__(param_spec)


class _DoubleParamValidator(_NumericalParamValidator):
    """
    ParamValidator class for a service_customization_pb2.DoubleParam.Spec

    Args:
        param_spec (service_customization_pb2.DoubleParam.Spec): The DoubleParam Spec this helper instance is being used for
    """
    proto_type = DoubleParam
    custom_param_value_field = "double_value"

    def __init__(self, param_spec):
        super().__init__(param_spec)


class _StringParamValidator(_ParamValidatorInterface):
    """
    ParamValidator class for a service_customization_pb2.StringParam.Spec

    Args:
        param_spec (service_customization_pb2.StringParam.Spec): The StringParam Spec this helper instance is being used for
    """
    proto_type = StringParam
    custom_param_value_field = "string_value"

    def __init__(self, param_spec):
        super().__init__(param_spec)

    def validate_spec(self):
        if self.param_spec.default_value and not self.param_spec.editable and self.param_spec.options and len(
                self.param_spec.options) > 0:
            if self.param_spec.default_value not in self.param_spec.options:
                raise InvalidCustomParamSpecError([
                    f"Default string {self.param_spec.default_value} not among options {self.param_spec.options}"
                ])

    def validate_value(self, param_value):
        err = check_types_match(param_value, self.proto_type)
        if err:
            return err

        if len(self.param_spec.options) > 0:
            if param_value.value not in self.param_spec.options:
                return CustomParamError(
                    status=CustomParamError.STATUS_INVALID_VALUE, error_messages=[
                        f"Chosen string value {param_value.value} not among options {self.param_spec.options}"
                    ])


class _BoolParamValidator(_ParamValidatorInterface):
    """
    ParamValidator class for a service_customization_pb2.BoolParam.Spec

    Args:
        param_spec (service_customization_pb2.BoolParam.Spec): The BoolParam Spec this helper instance is being used for
    """
    proto_type = BoolParam
    custom_param_field = "bool"

    def __init__(self, param_spec):
        super().__init__(param_spec)

    def validate_spec(self):
        return super().validate_spec()

    def validate_value(self, param_value):
        err = check_types_match(param_value, self.proto_type)
        if err:
            return err


class _RegionOfInterestParamValidator(_ParamValidatorInterface):
    """
    ParamValidator class for a service_customization_pb2.RegionOfInterestParam.Spec

    Args:
        param_spec (service_customization_pb2.RegionOfInterestParam.Spec): The RegionOfInterestParam Spec this helper instance is being used for
    """
    proto_type = RegionOfInterestParam
    custom_param_value_field = "roi_value"

    def __init__(self, param_spec):
        super().__init__(param_spec)

    def validate_spec(self):
        if not self.param_spec.allows_rectangle:
            if self.param_spec.default_area.rectangle:
                raise InvalidCustomParamSpecError(
                    ["Default area is a rectangle despite not being allowed"])

    def validate_value(self, param_value):
        err = check_types_match(param_value, self.proto_type)
        if err:
            return err

        if not self.param_spec.allows_rectangle:
            if param_value.area.rectangle:
                return CustomParamError(
                    status=CustomParamError.STATUS_INVALID_VALUE,
                    error_messages=["Chosen area is a rectangle despite not being allowed"])
        if param_value.image_cols < 0:
            return CustomParamError(status=CustomParamError.STATUS_INVALID_VALUE,
                                    error_messages=["Number of columns in image must be positive"])
        if param_value.image_rows < 0:
            return CustomParamError(status=CustomParamError.STATUS_INVALID_VALUE,
                                    error_messages=["Number of rows in image must be positive"])


class _ListParamValidator(_ParamValidatorInterface):
    """
    ParamValidator class for a service_customization_pb2.ListParam.Spec

    Args:
        param_spec (service_customization_pb2.ListParam.Spec): The ListParam Spec this helper instance is being used for
    """
    proto_type = ListParam
    custom_param_value_field = "list_value"

    def __init__(self, param_spec):
        super().__init__(param_spec)

    def validate_spec(self):
        # First check element_spec
        if not self.param_spec.HasField("element_spec"):
            raise InvalidCustomParamSpecError(["ListParam needs a defined element_spec"])
        element_spec_error = _CustomParamValidator(
            self.param_spec.element_spec).get_param_helper().validate_spec()
        if element_spec_error:
            raise InvalidCustomParamSpecError(
                _nested_error_message_helper("element_spec", element_spec_error.error_messages))

        # If that's valid, then check list bounds
        error_messages = []
        if (
                self.param_spec.HasField("min_number_of_values") and
                self.param_spec.HasField("max_number_of_values")
        ) and self.param_spec.min_number_of_values.value > self.param_spec.max_number_of_values.value:
            error_messages.append(
                f"Max ListParam.Spec size {self.param_spec.max_number_of_values} below minimum size of {self.param_spec.min_number_of_values}"
            )
        if self.param_spec.max_number_of_values.value < 0 or self.param_spec.min_number_of_values.value < 0:
            error_messages.append(
                f"Invalid negative list size bound, with (min, max) bound of {(self.param_spec.min_number_of_values.value, self.param_spec.max_number_of_values.value)}"
            )
        if error_messages:
            raise InvalidCustomParamSpecError(error_messages)

    def validate_value(self, param_value):
        err = check_types_match(param_value, self.proto_type)
        if err:
            return err

        if self.param_spec.HasField("min_number_of_values") and len(
                param_value.values) < self.param_spec.min_number_of_values.value:
            return CustomParamError(
                status=CustomParamError.STATUS_INVALID_VALUE, error_messages=[
                    f"ListParam has {len(param_value.values)} values, which is less than the required minimum {self.param_spec.min_number_of_values}"
                ])
        if self.param_spec.HasField("max_number_of_values") and len(
                param_value.values) > self.param_spec.max_number_of_values.value:
            return CustomParamError(
                status=CustomParamError.STATUS_INVALID_VALUE, error_messages=[
                    f"ListParam has {len(param_value.values)} values, which is more than the allowed maximum {self.param_spec.max_number_of_values}"
                ])
        custom_param_error = CustomParamError(status=CustomParamError.STATUS_OK)
        for custom_param_index in range(len(param_value.values)):
            custom_param = param_value.values[custom_param_index]
            spec_type = self.param_spec.element_spec.WhichOneof("spec")
            value_type = custom_param.WhichOneof("value")
            if spec_type.split("_")[0] != value_type.split("_")[0]:
                custom_param_error.status = CustomParamError.STATUS_INVALID_TYPE
                custom_param_error.error_messages.append(
                    f"Value is defined as {value_type} at index {custom_param_index} while the List Param Spec expects {spec_type}"
                )
                continue
            custom_param_value = getattr(custom_param, custom_param.WhichOneof("value"))
            error_proto = _CustomParamValidator(
                self.param_spec.element_spec).get_param_helper().validate_value(custom_param_value)
            if error_proto:
                custom_param_error.status = error_proto.status
                custom_param_error.error_messages.extend(
                    _nested_error_message_helper(f"[{custom_param_index}]",
                                                 error_proto.error_messages))
        if custom_param_error.status != CustomParamError.STATUS_OK:
            return custom_param_error


class _OneOfParamValidator(_ParamValidatorInterface):
    """
    ParamValidator class for a service_customization_pb2.OneOfInterestParam.Spec

    Args:
        param_spec (service_customization_pb2.OneOfInterestParam.Spec): The OneOfInterestParam Spec this helper instance is being used for
    """
    proto_type = OneOfParam
    custom_param_value_field = "one_of_value"

    def __init__(self, param_spec):
        super().__init__(param_spec)

    def validate_spec(self):
        if self.param_spec.default_key and self.param_spec.default_key not in self.param_spec.specs.keys(
        ):
            raise InvalidCustomParamSpecError(
                [f"OneOf parameter has nonexistent default key of {self.param_spec.default_key}"])
        custom_param_error = CustomParamError(status=CustomParamError.STATUS_OK)
        error_list = []
        for key, child_spec in self.param_spec.specs.items():
            try:
                _DictParamValidator(child_spec.spec).validate_spec()
            except InvalidCustomParamSpecError as e:
                error_list.extend(_nested_error_message_helper(key, e.args[0]))
        if error_list:
            raise InvalidCustomParamSpecError(error_list)

    def validate_value(self, param_value):
        err = check_types_match(param_value, self.proto_type)
        if err:
            return err

        if param_value.key not in self.param_spec.specs.keys():
            return CustomParamError(
                status=CustomParamError.STATUS_INVALID_VALUE,
                error_messages=[f"OneOf parameter value has nonexistent key of {param_value.key}"])

        # Only check active key since our spec doesn't guarantee valid values at unselected OneOf keys
        chosen_param_error = _DictParamValidator(
            self.param_spec.specs[param_value.key].spec).validate_value(
                param_value.values[param_value.key])
        if chosen_param_error:
            full_error = CustomParamError(
                status=chosen_param_error.status,
                error_messages=_nested_error_message_helper(param_value.key,
                                                            chosen_param_error.error_messages))
            return full_error


class _CustomParamValidator(_ParamValidatorInterface):
    """
    ParamValidator class for a service_customization_pb2.CustomParam.Spec

    Args:
        param_spec (service_customization_pb2.CustomParam.Spec): The CustomParam Spec this helper instance is being used for
    """
    custom_param_dict = {
        "dict_spec": _DictParamValidator,
        "list_spec": _ListParamValidator,
        "int_spec": _Int64ParamValidator,
        "double_spec": _DoubleParamValidator,
        "string_spec": _StringParamValidator,
        "roi_spec": _RegionOfInterestParamValidator,
        "bool_spec": _BoolParamValidator,
        "one_of_spec": _OneOfParamValidator
    }

    def __init__(self, param_spec):
        super().__init__(param_spec)
        self.sub_param_helper = self.get_param_helper()

    def get_param_helper(self):
        """
        Returns the ParamValidator instance for the defined OneOf spec in self.param_spec (a service_customization_pb2.CustomParam.Spec)
        """
        field_name = self.param_spec.WhichOneof('spec')
        return self.custom_param_dict[field_name](getattr(self.param_spec, field_name))

    def validate_spec(self):
        return self.sub_param_helper.validate_spec()

    def validate_value(self, param_value):
        return self.sub_param_helper.validate_value(
            getattr(param_value, self.sub_param_helper.custom_param_value_field))


def _nested_error_message_helper(child_name, child_error_messages):
    """
    Simple internal string helper function to take a list of errors from a child and return a list of errors
    for the parent, with each error specifying which child it came from.

    Args:
        child_name (string): The human-readable name of the child parameter in the parent's context.
            For DictParams and OneOfParams this is the parameter map's key, and for ListParams it's
            the index surrounded by brackets, such as "[1]"
        child_error_messages (list of strings): List of errors from the child with 'child_name'.
            In practice this will likely be copied directly from the "error_messages" field in the
            child param's service_customization_pb2.CustomParamError proto
    """
    joiner_string = " param has error: "
    for message_index, child_error in enumerate(child_error_messages):
        # If already nested, add child_name with period delimiter
        if joiner_string in child_error:
            child_error_messages[message_index] = child_name + "." + child_error
        # Else, make into a human-readable nested format
        else:
            child_error_messages[message_index] = child_name + joiner_string + child_error

        # Remove period delimiter for list indices
        child_error_messages[message_index] = child_error_messages[message_index].replace(".[", "[")
    return child_error_messages


def custom_spec_to_default(spec):
    """
    Create a default service_customization_pb2.CustomParam based off of the service_customization_pb2.CustomParam.Spec argument

    Args:
        spec (service_customization_pb2.CustomParam.Spec): spec to which the parameter should be defaulted
    """
    which_spec = spec.WhichOneof('spec')

    default_func = _SPEC_VALUES[which_spec][1]

    param_value = default_func(getattr(spec, which_spec))
    if param_value is None:
        return None

    if which_spec == 'dict_spec':
        return CustomParam(dict_value=param_value)
    elif which_spec == 'list_spec':
        return CustomParam(list_value=param_value)
    elif which_spec == 'int_spec':
        return CustomParam(int_value=param_value)
    elif which_spec == 'double_spec':
        return CustomParam(double_value=param_value)
    elif which_spec == 'string_spec':
        return CustomParam(string_value=param_value)
    elif which_spec == 'roi_spec':
        return CustomParam(roi_value=param_value)
    elif which_spec == 'bool_spec':
        return CustomParam(bool_value=param_value)
    elif which_spec == 'one_of_spec':
        return CustomParam(one_of_value=param_value)
    else:
        return None


def dict_spec_to_default(spec):
    """
    Create a default service_customization_pb2.DictParam based off of the service_customization_pb2.DictParam.Spec argument.

    Args:
        spec (service_customization_pb2.DictParam.Spec): spec to which the parameter should be defaulted
    """
    param = DictParam()
    for (key, value) in spec.specs.items():
        default_value_param = custom_spec_to_default(value.spec)
        if default_value_param is not None:
            param.values[key].CopyFrom(default_value_param)
    return param


def list_spec_to_default(spec):
    """
    Create a default service_customization_pb2.ListParam based off of the service_customization_pb2.ListParam.Spec argument

    Args:
        spec (service_customization_pb2.ListParam.Spec): spec to which the parameter should be defaulted
    """
    param = ListParam()
    default_element_spec = custom_spec_to_default(spec.element_spec)
    if default_element_spec is not None:
        for i in range(0, spec.min_number_of_values.value):
            param.values.append(default_element_spec)

    return param


def int_spec_to_default(spec):
    """
    Create a default service_customization_pb2.IntParam based off of the service_customization_pb2.IntParam.Spec argument

    Args:
        spec (service_customization_pb2.IntParam.Spec): spec to which the parameter should be defaulted
    """
    param = Int64Param()
    if spec.HasField('default_value'):
        param.value = spec.default_value.value
    elif spec.HasField('min_value'):
        param.value = spec.min_value.value
    elif spec.HasField('max_value'):
        param.value = spec.max_value.value
    else:
        param.value = 0
    return param


def double_spec_to_default(spec):
    """
    Create a default service_customization_pb2.DoubleParam based off of the service_customization_pb2.DoubleParam.Spec argument

    Args:
        spec (service_customization_pb2.DoubleParam.Spec): spec to which the parameter should be defaulted
    """
    param = DoubleParam()
    if spec.HasField('default_value'):
        param.value = spec.default_value.value
    elif spec.HasField('min_value'):
        param.value = spec.min_value.value
    elif spec.HasField('max_value'):
        param.value = spec.max_value.value
    else:
        param.value = 0
    return param


def string_spec_to_default(spec):
    """
    Create a default service_customization_pb2.StringParam based off of the service_customization_pb2.StringParam.Spec argument

    Args:
        spec (service_customization_pb2.StringParam.Spec): spec to which the parameter should be defaulted
    """
    param = StringParam()
    if spec.default_value != '':
        param.value = spec.default_value
    elif len(spec.options) > 0:
        param.value = spec.options[0]
    else:
        param.value = ''
    return param


def roi_spec_to_default(spec):
    """
    Create a default service_customization_pb2.RegionOfInterestParam based off of the service_customization_pb2.RegionOfInterestParam.Spec argument

    Args:
        spec (service_customization_pb2.RegionOfInterestParam.Spec): spec to which the parameter should be defaulted
    """
    if not spec.allows_rectangle:
        return None
    param = RegionOfInterestParam()
    if spec.HasField('default_area'):
        param.area.CopyFrom(spec.default_area)
    if spec.HasField('service_and_source'):
        param.service_and_source.CopyFrom(spec.service_and_source)
    return param


def bool_spec_to_default(spec):
    """
    Create a default service_customization_pb2.BoolParam based off of the service_customization_pb2.BoolParam.Spec argument

    Args:
        spec (service_customization_pb2.BoolParam.Spec): spec to which the parameter should be defaulted
    """
    return BoolParam(value=spec.default_value.value)


def one_of_spec_to_default(spec):
    """
    Create a default service_customization_pb2.OneOfParam based off of the service_customization_pb2.OneOfParam.Spec argument

    Args:
        spec (service_customization_pb2.OneOfParam.Spec): spec to which the parameter should be defaulted
    """
    param = OneOfParam()
    key = spec.default_key
    if key not in spec.specs.keys():
        return None

    param.key = key
    for (key, value) in spec.specs.items():
        param.values[key].CopyFrom(dict_spec_to_default(value.spec))
    return param


def dict_param_coerce_to(param, spec):
    """
    Coerce a service_customization_pb2.DictParam based off of the spec passed in. The parameter is modified in-place.

    Args:
        param (service_customization_pb2.DictParam): parameter that requires coercing
        spec (service_customization_pb2.DictParam.Spec): spec to which the parameter should be coerced

    Returns:
        `True` if parameter was coerced
        `False` otherwise
    """
    did_coerce = False
    new_map = {}
    for (key, child_spec) in spec.specs.items():
        p = param.values[key]
        if p is None:
            default_param = custom_spec_to_default(child_spec.spec)
            new_map[key] = default_param
            did_coerce = True
        else:
            if custom_param_coerce_to(p, child_spec.spec):
                did_coerce = True
            new_map[key] = p
    param.ClearField('values')
    for key in spec.specs.keys():
        param.values[key].CopyFrom(new_map[key])
    return did_coerce


def list_param_coerce_to(param, spec):
    """
    Coerce a service_customization_pb2.ListParam based off of the spec passed in. The parameter is modified in-place.

    Args:
        param (service_customization_pb2.ListParam): parameter that requires coercing
        spec (service_customization_pb2.ListParam.Spec): spec to which the parameter should be coerced

    Returns:
        `True` if parameter was coerced
        `False` otherwise
    """
    did_coerce = False
    if spec.HasField('min_number_of_values'):
        if len(param.values) < spec.min_number_of_values.value:
            default_element_param = custom_spec_to_default(spec.element_spec)
            param.values.extend(
                [default_element_param] * (spec.min_number_of_values.value - len(param.values)))
            did_coerce = True
    if spec.HasField('max_number_of_values'):
        while len(param.values) > spec.max_number_of_values.value:
            param.values.pop()
            did_coerce = True
    for i in range(0, len(param.values)):
        if custom_param_coerce_to(param.values[i], spec.element_spec):
            did_coerce = True
    return did_coerce


def int_param_coerce_to(param, spec):
    """
    Coerce a service_customization_pb2.IntParam based off of the spec passed in. The parameter is modified in-place.

    Args:
        param (service_customization_pb2.IntParam): parameter that requires coercing
        spec (service_customization_pb2.Int.Spec): spec to which the parameter should be coerced

    Returns:
        `True` if parameter was coerced
        `False` otherwise
    """
    invalid_max = spec.HasField('max_value') and param.value > spec.max_value.value
    invalid_min = spec.HasField('min_value') and param.value < spec.min_value.value
    if invalid_max or invalid_min:
        param.Clear()
        param.MergeFrom(int_spec_to_default(spec))
        return True
    return False


def double_param_coerce_to(param, spec):
    """
    Coerce a service_customization_pb2.CustomParam based off of the spec passed in. The parameter is modified in-place.

    Args:
        param (service_customization_pb2.DoubleParam): parameter that requires coercing
        spec (service_customization_pb2.DoubleParam.Spec): spec to which the parameter should be coerced

    Returns:
        `True` if parameter was coerced
        `False` otherwise
    """
    invalid_max = spec.HasField('max_value') and param.value > spec.max_value.value
    invalid_min = spec.HasField('min_value') and param.value < spec.min_value.value
    if invalid_max or invalid_min:
        param.Clear()
        param.MergeFrom(double_spec_to_default(spec))
        return True
    return False


def string_param_coerce_to(param, spec):
    """
    Coerce a service_customization_pb2.StringParam based off of the spec passed in. The parameter is modified in-place.

    Args:
        param (service_customization_pb2.StringParam): parameter that requires coercing
        spec (service_customization_pb2.StringParam.Spec): spec to which the parameter should be coerced

    Returns:
        `True` if parameter was coerced
        `False` otherwise
    """
    if not spec.editable and param.value not in spec.options and len(spec.options) > 0:
        param.Clear()
        param.MergeFrom(string_spec_to_default(spec))
        return True
    return False


def roi_param_coerce_to(param, spec):
    """
    Coercion is tricky with ROI parameters due to the fact that there is no standard frame size. ROI parameter is not
    modified in place; rather, a boolean value is returned.

    Args:
        param (service_customization_pb2.RegionOfInterestParam): parameter that requires coercing
        spec (service_customization_pb2.RegionOfInterestParam.Spec): spec to which the parameter should be coerced

    Returns:
        `True` if service_and_source is unset or if the spec and the parameter match
        `False` otherwise
    """
    return not spec.HasField(
        'service_and_source') or spec.service_and_source == param.service_and_source


def one_of_param_coerce_to(param, spec):
    """
    Coerce a service_customization_pb2.OneOfParam based off of the spec passed in. The parameter is modified in-place.

    Args:
        param (service_customization_pb2.OneOfParam): parameter that requires coercing
        spec (service_customization_pb2.OneOfParam.Spec): spec to which the parameter should be coerced

    Returns:
        `True` if parameter was coerced
        `False` otherwise
    """
    did_coerce = False
    if param.key not in spec.specs.keys():
        param.key = sorted(list(spec.specs.keys()))[0]
        did_coerce = True
    new_map = {}
    for (key, child_spec) in spec.specs.items():
        value_param = param.values[key]
        if value_param is None:
            new_map[key] = dict_spec_to_default(child_spec.spec)
            did_coerce = True
        else:
            if dict_param_coerce_to(value_param, child_spec.spec):
                did_coerce = True
            new_map[key] = value_param

    param.ClearField('values')
    for key in spec.specs.keys():
        param.values[key].CopyFrom(new_map[key])

    return did_coerce


_SPEC_VALUES = {
    'dict_spec': ('dict_value', dict_spec_to_default, dict_param_coerce_to),
    'list_spec': ('list_value', list_spec_to_default, list_param_coerce_to),
    'int_spec': ('int_value', int_spec_to_default, int_param_coerce_to),
    'double_spec': ('double_value', double_spec_to_default, double_param_coerce_to),
    'string_spec': ('string_value', string_spec_to_default, string_param_coerce_to),
    'roi_spec': ('roi_value', roi_spec_to_default, roi_param_coerce_to),
    'bool_spec':
        ('bool_value', bool_spec_to_default, None),  # No coercing, there are no illegal values.
    'one_of_spec': ('one_of_value', one_of_spec_to_default, one_of_param_coerce_to),
}


def custom_param_coerce_to(param, spec):
    """
    Coerce a service_customization_pb2.CustomParam based off of the spec passed in. The parameter is modified in-place.

    Args:
        param (service_customization_pb2.CustomParam): parameter that requires coercing
        spec (service_customization_pb2.CustomParam.Spec): spec to which the parameter should be coerced

    Returns:
        `True` if parameter was coerced
        `False` otherwise
    """
    did_coerce = False
    which_spec = spec.WhichOneof('spec')

    field_name, default_value_func, coercion_func = _SPEC_VALUES[which_spec]
    if param.HasField(field_name):
        if coercion_func is not None:
            if coercion_func(getattr(param, field_name), getattr(spec, which_spec)):
                did_coerce = True
    else:
        param.Clear()
        getattr(param, field_name).CopyFrom(default_value_func(getattr(spec, which_spec)))
        did_coerce = True
    return did_coerce


def make_custom_param_spec(
    spec: Union[DictParam.Spec, ListParam.Spec, Int64Param.Spec, DoubleParam.Spec, StringParam.Spec,
                RegionOfInterestParam.Spec, BoolParam.Spec, OneOfParam.Spec]
) -> CustomParam.Spec:
    """
    Helper function to create a CustomParam.Spec

    Args:
         spec: spec to be wrapped by a CustomParam.Spec
    """
    if isinstance(spec, DictParam.Spec):
        return CustomParam.Spec(dict_spec=spec)
    if isinstance(spec, ListParam.Spec):
        return CustomParam.Spec(list_spec=spec)
    if isinstance(spec, Int64Param.Spec):
        return CustomParam.Spec(int_spec=spec)
    if isinstance(spec, DoubleParam.Spec):
        return CustomParam.Spec(double_spec=spec)
    if isinstance(spec, StringParam.Spec):
        return CustomParam.Spec(string_spec=spec)
    if isinstance(spec, RegionOfInterestParam.Spec):
        return CustomParam.Spec(roi_spec=spec)
    if isinstance(spec, BoolParam.Spec):
        return CustomParam.Spec(bool_spec=spec)
    if isinstance(spec, OneOfParam.Spec):
        return CustomParam.Spec(one_of_spec=spec)
    raise ValueError('Must provide a spec from service_customization_pb2 to this function.')


def make_dict_child_spec(param_spec: Union[DictParam.Spec, ListParam.Spec, Int64Param.Spec,
                                           DoubleParam.Spec, StringParam.Spec,
                                           RegionOfInterestParam.Spec, BoolParam.Spec,
                                           OneOfParam.Spec],
                         ui_info: Optional[UserInterfaceInfo] = None) -> DictParam.ChildSpec:
    """
    Helper function to create a DictParam.ChildSpec

    Args:
         param_spec: spec for DictParam.ChildSpec that is converted into a CustomParam.Spec when forming the ChildSpec
         ui_info: instantiation of service_customization_pb2.UserInterfaceInfo
    """
    return DictParam.ChildSpec(spec=make_custom_param_spec(param_spec), ui_info=ui_info)


def make_dict_param_spec(specs: Dict[str, DictParam.ChildSpec],
                         is_hidden_by_default: bool) -> DictParam.Spec:
    """
    Helper function to create a DictParam.Spec

    Args:
         specs: specs contained by the DictParam
         is_hidden_by_default: controls whether the UI shows this spec as collapsed by default
    """
    return DictParam.Spec(specs=specs, is_hidden_by_default=is_hidden_by_default)


def make_one_of_child_spec(dict_param_spec: DictParam.Spec,
                           ui_info: Optional[UserInterfaceInfo] = None) -> OneOfParam.ChildSpec:
    """
    Helper function to create a OneOfParam.ChildSpec

    Args:
         dict_param_spec: spec for OneOfParam.ChildSpec
         ui_info: instantiation of service_customization_pb2.UserInterfaceInfo
    """
    return OneOfParam.ChildSpec(spec=dict_param_spec, ui_info=ui_info)


def make_one_of_param_spec(specs: Dict[str, OneOfParam.ChildSpec],
                           default_key: Optional[str] = None) -> OneOfParam.Spec:
    """
    Helper function to create a OneOfParam.Spec

    Args:
         specs: specs contained by the OneOfParam
         default_key: the key to which the OneOfParam.Spec should default in the UI
    """
    return OneOfParam.Spec(specs=specs, default_key=default_key)


def make_list_param_spec(element_spec: CustomParam.Spec, min_number_of_values: Optional[int] = None,
                         max_number_of_values: Optional[int] = None) -> ListParam.Spec:
    """
    Helper function to create a ListParam.Spec

    Args:
         element_spec: spec for each element of the list
         min_number_of_values: minimum number of elements in the list
         max_number_of_values: maximum number of elements in the list
    """
    spec = ListParam.Spec(element_spec=element_spec)
    if min_number_of_values is not None:
        spec.min_number_of_values.value = min_number_of_values
    if max_number_of_values is not None:
        spec.max_number_of_values.value = max_number_of_values
    return spec


def make_int64_param_spec(default_value: Optional[int] = None, units: Optional[Units] = None,
                          min_value: Optional[int] = None,
                          max_value: Optional[int] = None) -> Int64Param.Spec:
    """
    Helper function to create an Int64Param.Spec

    Args:
         default_value: starting value for Int64Param
         units: units of the Int64Param
         min_value: smallest value the Int64Param may be
         max_value: largest value the Int64Param may be
    """
    spec = Int64Param.Spec(units=units)
    if default_value is not None:
        spec.default_value.value = default_value
    if min_value is not None:
        spec.min_value.value = min_value
    if max_value is not None:
        spec.max_value.value = max_value
    return spec


def make_double_param_spec(default_value: Optional[float] = None, units: Optional[Units] = None,
                           min_value: Optional[float] = None,
                           max_value: Optional[float] = None) -> DoubleParam.Spec:
    """
    Helper function to create a DoubleParam.Spec

    Args:
         default_value: starting value for DoubleParam
         units: units of the DoubleParam
         min_value: smallest value the DoubleParam may be
         max_value: largest value the DoubleParam may be
    """
    spec = DoubleParam.Spec(units=units)
    if default_value is not None:
        spec.default_value.value = default_value
    if min_value is not None:
        spec.min_value.value = min_value
    if max_value is not None:
        spec.max_value.value = max_value
    return spec


def make_string_param_spec(options: Optional[List[str]] = None, editable: Optional[bool] = None,
                           default_value: Optional[str] = None) -> StringParam.Spec:
    """
    Helper function to create a StringParam.Spec

    Args:
         options: predetermined options the StringParam may be
         editable: whether the value may be edited
         default_value: initial value for StringParam
    """
    return StringParam.Spec(options=options, editable=editable, default_value=default_value)


def make_bool_param_spec(default_value: Optional[bool] = None) -> BoolParam.Spec:
    """
    Helper function to create an BoolParam.Spec

    Args:
         default_value: starting value for BoolParam
    """
    spec = BoolParam.Spec()
    if default_value is not None:
        spec.default_value.value = default_value
    return spec


def make_region_of_interest_param_spec(
        service_and_source: Optional[RegionOfInterestParam.ServiceAndSource] = None,
        default_area: Optional[AreaI] = None,
        allows_rectangle: bool = False) -> RegionOfInterestParam.Spec:
    """
    Helper function to create a RegionOfInterestParam.Spec

    Args:
         service_and_source: service and source to which the RegionOfInterestParam should adhere
         default_area: starting area for the RegionOfInterestParam
         allows_rectangle: whether a rectangle may be drawn for the selected area
    """
    return RegionOfInterestParam.Spec(default_area=default_area,
                                      service_and_source=service_and_source,
                                      allows_rectangle=allows_rectangle)




def make_user_interface_info(display_name: Optional[str] = None, description: Optional[str] = None,
                             display_order: Optional[int] = None) -> UserInterfaceInfo:
    """
    Helper function to create UserInterfaceInfo

    Args:
         display_name: human-readable name displayed by the UI
         description: additional information for parameter (used in conjunction with display_name)
         display_order: order in which the fields should be displayed
    """
    ui_info = UserInterfaceInfo()
    if display_name is not None:
        ui_info.display_name = display_name
    if description is not None:
        ui_info.description = description
    if display_order is not None:
        ui_info.display_order = display_order
    return ui_info


def make_roi_service_and_source(service: str,
                                source: str) -> RegionOfInterestParam.ServiceAndSource:
    """
    Helper function to create a RegionOfInterestParam.ServiceAndSource

    Args:
         service: the ImageService providing the image
         source: the ImageSource providing the image
    """
    return RegionOfInterestParam.ServiceAndSource(service=service, source=source)
