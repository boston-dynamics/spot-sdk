# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from __future__ import unicode_literals

from builtins import str as text

from bosdyn.mission import util


class Error(Exception):
    """Base exception"""


class CompileError(Error):
    """Error occurred during compilation."""

    def __init__(self, msg='', node_proto=None):
        Error.__init__(self, msg)
        self.node_proto = node_proto

    def node_name(self):
        """Returns the 'name' field of the Node proto if possible, None otherwise"""
        if self.node_proto is None:
            return None
        try:
            return self.node_proto.name
        except Exception:
            return None

    def node_impl(self):
        """Returns the proto type of the Node 'impl' field if possible, None otherwise"""
        if self.node_proto is None:
            return None
        try:
            return self.node_proto.impl.TypeName()
        except Exception:
            return None

    def get_node_details(self):
        """Get a string of the node detail."""
        details = ''
        node_impl = self.node_impl()
        if node_impl:
            details = f' ({node_impl}'

        node_name = self.node_name()
        if node_name is not None:
            if not details:
                details = ' (???'
            details += f' with name "{node_name}")'
        return details

    def __str__(self):
        msg = super(CompileError, self).__str__()
        return msg + self.get_node_details()


class UnknownType(CompileError):

    def __str__(self):
        return 'Do not know how to build {}'.format(self.node_impl())


class ValidationError(Error):
    """The mission encountered errors in the validate step.

        Args:
          tree: The root node of the compiled mission.
          errors: List of ValidationErrorReport.
    """

    def __init__(self, tree, errors):
        self.tree = tree
        self.errors = errors

    def __str__(self):
        return 'Encountered {} validation errors: \n\t{}'.format(
            len(self.errors), '\n\t'.join([text(e) for e in self.errors]))


class MissingParameterError(CompileError):
    """Could not find a matching parameter.

        Args:
          target_name: Name of the parameter that was missing / mismatched.
          target_pb_type: Desired type of the parameter. None if any type was acceptable.
          stored_pb_type: Type of the parameter that was stored. None if type was unknown.
    """

    def __init__(self, target_name, target_pb_type=None, stored_pb_type=None):
        self.target_name = target_name
        self.target_pb_type = target_pb_type
        self.stored_pb_type = stored_pb_type

    def __str__(self):
        if self.target_pb_type != self.stored_pb_type:
            return 'Mismatched type for "{}". Stored as {}, wanted {}'.format(
                self.target_name, util.safe_pb_type_to_string(self.stored_pb_type),
                util.safe_pb_type_to_string(self.target_pb_type))
        return 'No parameter "{}"'.format(self.target_name)


class InaccessibleParameterError(MissingParameterError):
    """Could not read the parameter, though one was provided elsewhere."""


class MessageOverrideError(CompileError):
    """Failed to override a mission node's field with a Message type."""

    def __init__(self, overriding_message, field_name, field_type):
        self.overriding_message = overriding_message
        self.field_name = field_name
        self.field_type = field_type

    def __str__(self):
        return 'Override of type {} cannot be written to field "{}" of type {}'.format(
            self.overriding_message.TypeName(), self.field_name, self.field_type)


class NodeUnreferenceableError(Error):
    """Node cannot be referenced."""


