# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from __future__ import unicode_literals
from builtins import str as text
import copy
import operator
import re
import six
import google.protobuf.message
import google.protobuf.text_format

from bosdyn.api.mission import mission_pb2, nodes_pb2, util_pb2
from bosdyn.api.graph_nav import graph_nav_pb2
from bosdyn.mission import constants

# This is a special dummy message we'll use for TYPE_MESSAGE parameters.
DUMMY_MESSAGE = nodes_pb2.Node(name='dummy-message-for-parameterization')


class Error(Exception):
    pass


class InvalidConversion(Error):
    """Could not convert the provided value to the destination type."""

    def __init__(self, original_value, destination_typename):
        self.original_value = original_value
        self.destination_typename = destination_typename

    def __str__(self):
        return 'Could not convert "{}" to type "{}"'.format(self.original_value, self.destination_typename)


_python_identifier_regex = re.compile('[A-Za-z_]\w*$')


def tree_to_string(root, start_level=0, include_status=False):
    """Get a string representation of a Node, interpreted as a tree."""
    string = ''
    if start_level == 0:
        string += '\n'
    prefix = '|' + '-' * start_level
    string += prefix + text(root) + (' ' if text(root) else '') + '(' + root.__class__.__name__ + ')'
    if include_status:
        string += '\n' + prefix + 'Status code: [{}]'.format(root.last_result)
    for child in root.children:
        string += '\n' + tree_to_string(child, start_level=start_level + 1,
                                        include_status=include_status)
    return string


def proto_from_tuple(tup):
    """Return a bosdyn.api.mission Node from a tuple. EXPERIMENTAL.

    Example:
    ::
    ('do-A-then-B', bosdyn.api.mission.nodes_pb2.Sequence(always_restart=True),
    [
    ('A', foo.bar.Command(...), []),
    ('B', foo.bar.Command(...), []),
    ]
    )
    would make a Sequence named 'do-A-then-B' that always restarted, executing some Command
    named 'A' followed by the Command named 'B'. NOTE: The "List of children tuples" will only
    work if the parent node has 'child' or 'children' attributes. See tests/test_util.py for a
    longer example.

    Args:
        tup: (Name of node, Instantiated implementation of node protobuf, List of children tuples)
    """
    node = nodes_pb2.Node()

    name_or_dict, inner_proto, children = tup
    if isinstance(name_or_dict, dict):
        node.name = name_or_dict.get('name', '')
        node.reference_id = name_or_dict.get('reference_id', '')
        node.node_reference = name_or_dict.get('node_reference', '')
        if 'user_data' in name_or_dict:
            node.user_data.CopyFrom(name_or_dict['user_data'])

        for name, pb_type in six.iteritems(name_or_dict.get('parameters', {})):
            parameter = util_pb2.VariableDeclaration(name=name, type=pb_type)
            node.parameters.add().CopyFrom(parameter)

        for key, value in six.iteritems(name_or_dict.get('parameter_values', {})):
            parameter_value = util_pb2.KeyValue(key=key)
            if isinstance(value, six.string_types) and value[0] == '$':
                parameter_value.value.parameter.name = value[1:]
                # Leave type unspecified, since we can't look it up easily yet.
            else:
                parameter_value.value.constant.CopyFrom(python_var_to_value(value))
            node.parameter_values.add().CopyFrom(parameter_value)

        for key, value in six.iteritems(name_or_dict.get('overrides', {})):
            # Rather than keep this matching the compiler functionality, just omit the check.
            # It's not even a CompileError anyway.
            #if key not in inner_proto.DESCRIPTOR.fields_by_name:
            #    raise CompileError('Override specified for "{}" but no such field in "{}"'.format(
            #        key, inner_proto.DESCRIPTOR.full_name))
            override = util_pb2.KeyValue(key=key)
            override.value.parameter.name = value
            # We do need the final field for setting the type accurately...
            #override.value.parameter.type = field_desc_to_pb_type(inner_proto.DESCRIPTOR.fields_by_name[key])

            node.overrides.add().CopyFrom(override)
    else:
        node.name = name_or_dict

    if node.node_reference:
        return node

    num_children = len(children)
    inner_type = inner_proto.DESCRIPTOR.name

    # Do some sanity checking on the children.
    if hasattr(inner_proto, 'children'):
        if num_children == 0:
            raise Error('Proto "{}" of type "{}" has no children!'.format(node.name, inner_type))
    elif hasattr(inner_proto, 'child'):
        if num_children != 1:
            raise Error('Proto "{}" of type "{}" has {} children!'.format(
                node.name, inner_type, num_children))
    elif num_children != 0:
        raise Error('Proto "{}" of type "{}" was given {} children, but I do not know how to add'
                    ' them!'.format(node.name, inner_type, num_children))

    for child_tup in children:
        child_node = proto_from_tuple(child_tup)
        if hasattr(inner_proto, 'children'):
            inner_proto.children.add().CopyFrom(child_node)
        elif hasattr(inner_proto, 'child'):
            inner_proto.child.CopyFrom(child_node)

    node.impl.Pack(inner_proto)
    return node


def python_var_to_value(var):
    """Returns a ConstantValue with the appropriate oneof set."""
    value = util_pb2.ConstantValue()
    if isinstance(var, bool):
        value.bool_value = var
    elif isinstance(var, six.integer_types):
        value.int_value = var
    elif isinstance(var, float):
        value.float_value = var
    elif isinstance(var, six.string_types):
        value.string_value = var
    elif isinstance(var, google.protobuf.message.Message):
        value.msg_value.Pack(var)
    else:
        raise Error('Invalid type "{}"'.format(type(var)))
    return value


def python_type_to_pb_type(var):
    """Returns the protobuf-schema variable type that corresponds to the given variable."""
    if isinstance(var, bool):
        return util_pb2.VariableDeclaration.TYPE_BOOL
    elif isinstance(var, six.integer_types):
        return util_pb2.VariableDeclaration.TYPE_INT
    elif isinstance(var, float):
        # Python floating point is typically a C double.
        return util_pb2.VariableDeclaration.TYPE_FLOAT
    elif isinstance(var, six.string_types):
        return util_pb2.VariableDeclaration.TYPE_STRING
    elif isinstance(var, google.protobuf.message.Message):
        return util_pb2.VariableDeclaration.TYPE_MESSAGE
    raise InvalidConversion(var, util_pb2.VariableDeclaration.Type.DESCRIPTOR.full_name)


def is_string_identifier(string):
    if hasattr(string, 'isidentifier'):
        return string.isidentifier()
    return bool(_python_identifier_regex.match(string))


def field_desc_to_pb_type(field_desc):
    """Returns the protobuf-schema variable type that corresponds to the given descriptor."""
    if field_desc.type in (field_desc.TYPE_UINT32, field_desc.TYPE_UINT64, field_desc.TYPE_FIXED32,
                           field_desc.TYPE_FIXED64, field_desc.TYPE_INT32, field_desc.TYPE_INT64,
                           field_desc.TYPE_SFIXED64, field_desc.TYPE_SINT32, field_desc.TYPE_SINT64,
                           field_desc.TYPE_SFIXED32):
        return util_pb2.VariableDeclaration.TYPE_INT
    elif field_desc.type in (field_desc.TYPE_DOUBLE, field_desc.TYPE_FLOAT):
        return util_pb2.VariableDeclaration.TYPE_FLOAT
    elif field_desc.type == field_desc.TYPE_BOOL:
        return util_pb2.VariableDeclaration.TYPE_BOOL
    elif field_desc.type == field_desc.TYPE_STRING:
        return util_pb2.VariableDeclaration.TYPE_STRING
    elif field_desc.type == field_desc.TYPE_MESSAGE:
        return util_pb2.VariableDeclaration.TYPE_MESSAGE
    raise InvalidConversion(field_desc.type, util_pb2.VariableDeclaration.Type.DESCRIPTOR.full_name)


def safe_pb_type_to_string(pb_type):
    """Return the stringified VariableDeclaration.Type, or "<unknown>" if the type is invalid."""
    try:
        return util_pb2.VariableDeclaration.Type.Name(pb_type)
    except ValueError:
        return '<unknown>'


def one_line_str(msg):
    return google.protobuf.text_format.MessageToString(msg, as_one_line=True)


def node_spec_to_short_string(node_spec, maxlen=15):
    if node_spec.name:
        string = node_spec.name
    else:
        string = one_line_str(node_spec)
    if len(string) > maxlen:
        return string[0:maxlen - 3] + '...'
    return string


class ResultFromProto:
    results_from_proto = {
        util_pb2.RESULT_FAILURE: constants.Result.FAILURE,
        util_pb2.RESULT_RUNNING: constants.Result.RUNNING,
        util_pb2.RESULT_SUCCESS: constants.Result.SUCCESS,
        util_pb2.RESULT_ERROR: constants.Result.ERROR,
    }

    proto_from_results = {v: k for k, v in six.iteritems(results_from_proto)}


def proto_enum_to_result_constant(proto_msg):
    """Returns a Result enum from a util_pb2.Result, or throws InvalidConversion error."""
    try:
        return ResultFromProto.results_from_proto[proto_msg]
    except KeyError:
        raise InvalidConversion(proto_msg, 'constants.Result')


def result_constant_to_proto_enum(result):
    """Returns a protobuf version of the Result enum, RESULT_UNKNOWN on error."""
    if not isinstance(result, constants.Result):
        raise InvalidConversion(result, util_pb2.Result.DESCRIPTOR.full_name)
    try:
        return ResultFromProto.proto_from_results[result]
    except KeyError:
        raise InvalidConversion(result, util_pb2.Result.DESCRIPTOR.full_name)


def most_restrictive_travel_params(travel_params, vel_limit=None):
    if travel_params is None:
        travel_params = graph_nav_pb2.TravelParams()
    else:
        travel_params = copy.deepcopy(travel_params)

    def take_limiting(mine, other, compare):
        # This is basically a hack to deal with proto3's handling of unset POD.
        # All float and integer fields that are unset in a message will have a value of 0.
        if other == 0:
            return mine
        if mine == 0:
            return other
        if compare(mine, other):
            return other
        return mine

    def take_velocity_limit(returned, other):
        # Look at max_vel using >=, then min_vel using <=.
        for min_max, comp in (('max_vel', operator.ge), ('min_vel', operator.le)):
            # If the other doesn't even have this field, skip to the next one.
            if not other.HasField(text(min_max)):
                continue

            lim_returned = getattr(returned, min_max)
            lim_other = getattr(other, min_max)
            lim_returned.linear.x = take_limiting(lim_returned.linear.x, lim_other.linear.x, comp)
            lim_returned.linear.y = take_limiting(lim_returned.linear.y, lim_other.linear.y, comp)
            lim_returned.angular = take_limiting(lim_returned.angular, lim_other.angular, comp)

    if vel_limit is not None:
        take_velocity_limit(travel_params.velocity_limit, vel_limit)
    return travel_params


def get_value_from_constant_value_message(const_proto):
    field = const_proto.WhichOneof('value')
    if field is None:
        raise AttributeError('Did not have a value set!')
    value = getattr(const_proto, field)
    return value


def get_value_from_value_message(node, blackboard, value_msg):
    if value_msg.HasField(text("constant")):
        constant = value_msg.constant
        return get_value_from_constant_value_message(constant)
    elif value_msg.HasField(text("runtime_var")):
        return blackboard.read(node, value_msg.runtime_var.name)
    else:
        raise AttributeError("Value must be a runtime variable or constant.")


def safe_pb_enum_to_string(value, pb_enum_obj):
    try:
        return pb_enum_obj.Name(value)
    except ValueError:
        pass
    return '<unknown> (value: {})'.format(value)
