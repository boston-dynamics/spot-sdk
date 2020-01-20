"""Client for the log-annotation service.

This allows client code to add operator comments and text-messages to the robot's log files.
"""

from __future__ import print_function
import logging

# Get LogAnnotationTextMessage so it can be imported from this package.
from bosdyn.api.log_annotation_pb2 import LogAnnotationTextMessage  #pylint: disable=unused-import
import bosdyn.api.log_annotation_service_pb2 as log_annotation_protos
import bosdyn.api.log_annotation_service_pb2_grpc as log_annotation_service

from .common import BaseClient, common_header_errors

LOGGER = logging.getLogger('log_annotation')


class LogAnnotationClient(BaseClient):
    """A client adding annotations to robot logs."""

    # http://google.github.io/styleguide/pyguide.html#3164-guidelines-derived-from-guidos-recommendations
    default_authority = "log.spot.robot"
    default_service_name = 'log-annotation'
    service_type = 'bosdyn.api.LogAnnotation'

    def __init__(self):
        super(LogAnnotationClient, self).__init__(log_annotation_service.LogAnnotationServiceStub)

    def add_operator_comment(self, msg, robot_timestamp=None, **kw_args):
        """Add an operator comment to the robot log

        Args:
          msg:                  Text of user comment to log.
          robot_timestamp:      Time (google.protobuf.Timestamp) of messages, in *robot time*.
                                If not set, timestamp will be when the robot receives the message.
          kw_args:              Extra arguments to pass to grpc call invocation.
        """
        request = log_annotation_protos.AddLogAnnotationRequest()
        request.annotations.operator_messages.add(message=msg, timestamp=robot_timestamp)
        return self.call(self._stub.AddLogAnnotation, request, value_from_response=None,
                         error_from_response=common_header_errors, **kw_args)

    def add_text_messages(self, text_messages, **kw_args):
        """Log text messages to the robot.

        Args:
          text_messages:  Sequence of LogAnnotationTextMessage protos.
          kw_args:        Extra arguments to pass to grpc call invocation.
        """

        request = log_annotation_protos.AddLogAnnotationRequest()
        for in_text_msg in text_messages:
            request.annotations.text_messages.add().CopyFrom(in_text_msg)

        return self.call(self._stub.AddLogAnnotation, request, value_from_response=None,
                         error_from_response=common_header_errors, **kw_args)
