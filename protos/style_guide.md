# Boston Dynamics API Protobuf Guidelines

The protobuf messages and service definitions are the primary interface definition for the Boston Dynamics API. Consistency in the definitions makes the API easier to understand and develop for.

**Proto3 only**. All services and messages must use proto3 only. This lets us reach the widest possible set of target platforms, and gives consistency.

**Follow Google protobuf style guide**. Their style guide is very thin, our APIs support it. https://developers.google.com/protocol-buffers/docs/style

**Use “Service” suffix for service definitions**. This makes it easier in generated code to disambiguate service names from message names.

**Use RequestHeader and ResponseHeader as first fields in requests and responses**. This gives a consistent way to collect timing information, common errors such as bad input, and other common handling techniques. Libraries for different languages exists to simplify handling these.

**Follow common error approach**. gRPC errors are used for transport-level issues such as networking problems or bad authorization tokens - which means service implementations almost always want to return gRPC Status OK. Internal service issues - like preconditions not being set - should use INTERNAL_SERVER_ERROR in the common ResponseHeader with optional error text string. Incorrectly formed request messages which are due to client programming errors should use INVALID_REQUEST in the common ResponseHeader with optional error text string. All other response statuses should use a response message specific Status enum.
 
**Times are represented with google.protobuf.Timestamp, and are all in “robot time”.** All timestamps are in the robot’s wall clock basis, and use the Timestamp object to represent the time. A separate TimeSync service exists to keep clients and robot in sync on time.

**Use MKS units for physical quantities.** Use the [MKS](http://scienceworld.wolfram.com/physics/MKS.html) system of units for physical quantities to be consistent with the rest of the API. Angular variables should be in radians rather than degrees.

**Enums should have an UNKNOWN entry at 0, and other values after that**. Proto3 uses 0 enum values when a variable is unset, so reserve that enum value for UNKNOWN. In general, this value should never be written and be treated as an error on read.

**Enums should be prefixed by their enum type**. For example, if UNKNOWN is part of enum "Status", the enum value should be STATUS_UNKNOWN. This supports Python behavior, where enums values are not scoped by the enum name.

**Use a “Proto” suffix for java_outer_classname option**. By default, Java’s protobuf compiler will create FooOuterClass when there is a file foo.proto containing a message Foo. Specify option java_outer_classname = “FooProto”; so the naming rationale is easier to figure out. [Java Generated Code](https://developers.google.com/protocol-buffers/docs/reference/java-generated#invocation)

**Document interfaces and messages**. The proto definitions effectively define the protocol of the API - be sure to document what each field means and what units it is in terms of. Ideally each service will also be unit-tested, and have tutorial code for how to use it. If conceptually difficult to understand, a concepts doc should also be included.

**Packages**. In addition to the Google style guide, we have a few additional guidelines for the "package" directive:

* Packages are all lowercase.
* Each package level should be one word.
* A .proto file's package declaration should match its relative path in the protos/ subdirectory. This is so the Python module namespace agrees with languages that obey the package directive.
* Flatter is better. For example, prefer bosdyn.api.spot over bosdyn.api.robot.spot.
* Consider creating a new package for messages and services which should be distributed separately and versioned separately. For example, services for a particular robot might be packaged separately from core API infrastructure.

**Put Request/Response messages alongside the service definitions** This tends to keep proto dependencies cleaner, and the service RPCs easier to understand.

**Consider package/namespace when naming messages** A message in the bosdyn.api.spot package doesn't need a "Spot" prefix in its name.
