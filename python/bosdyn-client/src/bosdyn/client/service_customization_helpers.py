# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from abc import ABC, abstractmethod
from typing import Callable, Optional

from bosdyn.api import service_customization_pb2


class InvalidCustomParamSpecError(ValueError):
    """Error indicating that the defined custom parameter Spec is invalid,
    with a list of error messages explaining why the spec is invalid"""


def validate_dict_spec(dict_spec: service_customization_pb2.DictParam.Spec) -> None:
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
    dict_spec: service_customization_pb2.DictParam.Spec
) -> Callable[[service_customization_pb2.DictParam],
              Optional[service_customization_pb2.CustomParamError]]:
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
    def validate_value(self, param_value) -> Optional[service_customization_pb2.CustomParamError]:
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
    proto_type = service_customization_pb2.DictParam
    custom_param_value_field = "dict_value"

    def __init__(self, param_spec):
        super().__init__(param_spec)

    def validate_spec(self):
        custom_param_error = service_customization_pb2.CustomParamError(
            status=service_customization_pb2.CustomParamError.STATUS_OK)
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
        value_keys = set(param_value.values.keys())
        spec_keys = set(self.param_spec.specs.keys())
        if not value_keys.issubset(spec_keys):
            return service_customization_pb2.CustomParamError(
                status=service_customization_pb2.CustomParamError.STATUS_UNSUPPORTED_PARAMETER,
                error_messages=[
                    f"DictParam value contains keys {value_keys - spec_keys} not present in the spec."
                ])
        custom_param_error = service_customization_pb2.CustomParamError(
            status=service_customization_pb2.CustomParamError.STATUS_OK)
        for name, custom_param in param_value.values.items():
            child_spec = self.param_spec.specs[name].spec
            child_value = getattr(custom_param, custom_param.WhichOneof("value"))
            error_proto = _CustomParamValidator(child_spec).get_param_helper().validate_value(
                child_value)
            if error_proto:
                custom_param_error.status = error_proto.status
                custom_param_error.error_messages.extend(
                    _nested_error_message_helper(name, error_proto.error_messages))
        if custom_param_error.status != service_customization_pb2.CustomParamError.STATUS_OK:
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
        num_value = param_value.value

        if self.param_spec.HasField("min_value"):
            if num_value < self.param_spec.min_value.value:
                return service_customization_pb2.CustomParamError(
                    status=service_customization_pb2.CustomParamError.STATUS_INVALID_VALUE,
                    error_messages=[
                        f"Value {num_value} below min_bound {self.param_spec.min_value.value}"
                    ])
        if self.param_spec.HasField("max_value"):
            if num_value > self.param_spec.max_value.value:
                return service_customization_pb2.CustomParamError(
                    status=service_customization_pb2.CustomParamError.STATUS_INVALID_VALUE,
                    error_messages=[
                        f"Value {num_value} above max_bound {self.param_spec.max_value.value}"
                    ])


class _Int64ParamValidator(_NumericalParamValidator):
    """
    ParamValidator class for a service_customization_pb2.Int64Param.Spec

    Args:
        param_spec (service_customization_pb2.Int64Param.Spec): The Int64Param Spec this helper instance is being used for
    """

    proto_type = service_customization_pb2.Int64Param
    custom_param_value_field = "int_value"

    def __init__(self, param_spec):
        super().__init__(param_spec)


class _DoubleParamValidator(_NumericalParamValidator):
    """
    ParamValidator class for a service_customization_pb2.DoubleParam.Spec

    Args:
        param_spec (service_customization_pb2.DoubleParam.Spec): The DoubleParam Spec this helper instance is being used for
    """
    proto_type = service_customization_pb2.DoubleParam
    custom_param_value_field = "double_value"

    def __init__(self, param_spec):
        super().__init__(param_spec)


class _StringParamValidator(_ParamValidatorInterface):
    """
    ParamValidator class for a service_customization_pb2.StringParam.Spec

    Args:
        param_spec (service_customization_pb2.StringParam.Spec): The StringParam Spec this helper instance is being used for
    """
    proto_type = service_customization_pb2.StringParam
    custom_param_value_field = "string_value"

    def __init__(self, param_spec):
        super().__init__(param_spec)

    def validate_spec(self):
        if self.param_spec.default_value and self.param_spec.options and len(
                self.param_spec.options) > 0:
            if self.param_spec.default_value not in self.param_spec.options:
                raise InvalidCustomParamSpecError([
                    f"Default string {self.param_spec.default_value} not among options {self.param_spec.options}"
                ])

    def validate_value(self, param_value):
        if len(self.param_spec.options) > 0:
            if param_value.value not in self.param_spec.options:
                return service_customization_pb2.CustomParamError(
                    status=service_customization_pb2.CustomParamError.STATUS_INVALID_VALUE,
                    error_messages=[
                        f"Chosen string value {param_value.value} not among options {self.param_spec.options}"
                    ])


class _BoolParamValidator(_ParamValidatorInterface):
    """
    ParamValidator class for a service_customization_pb2.BoolParam.Spec

    Args:
        param_spec (service_customization_pb2.BoolParam.Spec): The BoolParam Spec this helper instance is being used for
    """
    proto_type = service_customization_pb2.BoolParam
    custom_param_field = "bool"

    def __init__(self, param_spec):
        super().__init__(param_spec)

    def validate_spec(self):
        return super().validate_spec()

    def validate_value(self, param_value):
        return super().validate_value(param_value)


class _RegionOfInterestParamValidator(_ParamValidatorInterface):
    """
    ParamValidator class for a service_customization_pb2.RegionOfInterestParam.Spec

    Args:
        param_spec (service_customization_pb2.RegionOfInterestParam.Spec): The RegionOfInterestParam Spec this helper instance is being used for
    """
    proto_type = service_customization_pb2.RegionOfInterestParam
    custom_param_value_field = "roi_value"

    def __init__(self, param_spec):
        super().__init__(param_spec)

    def validate_spec(self):
        if not self.param_spec.allows_rectangle:
            if self.param_spec.default_area.rectangle:
                raise InvalidCustomParamSpecError(
                    ["Default area is a rectangle despite not being allowed"])

    def validate_value(self, param_value):
        if not self.param_spec.allows_rectangle:
            if param_value.area.rectangle:
                return service_customization_pb2.CustomParamError(
                    status=service_customization_pb2.CustomParamError.STATUS_INVALID_VALUE,
                    error_messages=["Chosen area is a rectangle despite not being allowed"])
        if param_value.image_cols < 0:
            return service_customization_pb2.CustomParamError(
                status=service_customization_pb2.CustomParamError.STATUS_INVALID_VALUE,
                error_messages=["Number of columns in image must be positive"])
        if param_value.image_rows < 0:
            return service_customization_pb2.CustomParamError(
                status=service_customization_pb2.CustomParamError.STATUS_INVALID_VALUE,
                error_messages=["Number of rows in image must be positive"])


class _ListParamValidator(_ParamValidatorInterface):
    """
    ParamValidator class for a service_customization_pb2.ListParam.Spec

    Args:
        param_spec (service_customization_pb2.ListParam.Spec): The ListParam Spec this helper instance is being used for
    """
    proto_type = service_customization_pb2.ListParam
    custom_param_value_field = "list_value"

    def __init__(self, param_spec):
        super().__init__(param_spec)

    def validate_spec(self):
        #First check element_spec
        if not self.param_spec.HasField("element_spec"):
            raise InvalidCustomParamSpecError(["ListParam needs a defined element_spec"])
        element_spec_error = _CustomParamValidator(
            self.param_spec.element_spec).get_param_helper().validate_spec()
        if element_spec_error:
            raise InvalidCustomParamSpecError(
                _nested_error_message_helper("element_spec", element_spec_error.error_messages))

        #If that's valid, then check list bounds
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
        if self.param_spec.HasField("min_number_of_values") and len(
                param_value.values) < self.param_spec.min_number_of_values.value:
            return service_customization_pb2.CustomParamError(
                status=service_customization_pb2.CustomParamError.STATUS_INVALID_VALUE,
                error_messages=[
                    f"ListParam has {len(param_value.values)} values, which is less than the required minimum {self.param_spec.min_number_of_values}"
                ])
        if self.param_spec.HasField("max_number_of_values") and len(
                param_value.values) > self.param_spec.max_number_of_values.value:
            return service_customization_pb2.CustomParamError(
                status=service_customization_pb2.CustomParamError.STATUS_INVALID_VALUE,
                error_messages=[
                    f"ListParam has {len(param_value.values)} values, which is more than the allowed maximum {self.param_spec.max_number_of_values}"
                ])
        custom_param_error = service_customization_pb2.CustomParamError(
            status=service_customization_pb2.CustomParamError.STATUS_OK)
        for custom_param_index in range(len(param_value.values)):
            custom_param = param_value.values[custom_param_index]
            spec_type = self.param_spec.element_spec.WhichOneof("spec")
            value_type = custom_param.WhichOneof("value")
            if spec_type.split("_")[0] != value_type.split("_")[0]:
                custom_param_error.status = service_customization_pb2.CustomParamError.STATUS_INVALID_TYPE
                custom_param_error.error_messages.append(
                    "Value is defined as {value_type} at index {custom_param_index} while the List Param Spec expects {spec_type}"
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
        if custom_param_error.status != service_customization_pb2.CustomParamError.STATUS_OK:
            return custom_param_error


class _OneOfParamValidator(_ParamValidatorInterface):
    """
    ParamValidator class for a service_customization_pb2.OneOfInterestParam.Spec

    Args:
        param_spec (service_customization_pb2.OneOfInterestParam.Spec): The OneOfInterestParam Spec this helper instance is being used for
    """
    proto_type = service_customization_pb2.OneOfParam
    custom_param_value_field = "one_of_value"

    def __init__(self, param_spec):
        super().__init__(param_spec)

    def validate_spec(self):
        if self.param_spec.default_key and self.param_spec.default_key not in self.param_spec.specs.keys(
        ):
            raise InvalidCustomParamSpecError(
                [f"OneOf parameter has nonexistent default key of {self.param_spec.default_key}"])
        custom_param_error = service_customization_pb2.CustomParamError(
            status=service_customization_pb2.CustomParamError.STATUS_OK)
        error_list = []
        for key, child_spec in self.param_spec.specs.items():
            try:
                _DictParamValidator(child_spec.spec).validate_spec()
            except InvalidCustomParamSpecError as e:
                error_list.extend(_nested_error_message_helper(key, e.args[0]))
        if error_list:
            raise InvalidCustomParamSpecError(error_list)

    def validate_value(self, param_value):
        if param_value.key not in self.param_spec.specs.keys():
            return service_customization_pb2.CustomParamError(
                status=service_customization_pb2.CustomParamError.STATUS_INVALID_VALUE,
                error_messages=[f"OneOf parameter value has nonexistent key of {param_value.key}"])

        #Only check active key since our spec doesn't guarantee valid values at unselected OneOf keys
        chosen_param_error = _DictParamValidator(
            self.param_spec.specs[param_value.key].spec).validate_value(
                param_value.values[param_value.key])
        if chosen_param_error:
            full_error = service_customization_pb2.CustomParamError(
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
        #If already nested, add child_name with period delimiter
        if joiner_string in child_error:
            child_error_messages[message_index] = child_name + "." + child_error
        #Else, make into a human-readable nested format
        else:
            child_error_messages[message_index] = child_name + joiner_string + child_error

        # Remove period delimiter for list indices
        child_error_messages[message_index] = child_error_messages[message_index].replace(".[", "[")
    return child_error_messages
