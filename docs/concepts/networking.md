<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Networking

All applications speak to Spot's API over a network connection. Understanding networking protocols is critical to debugging issues and creating a robust, high-performant application.

## Network Choice

Spot offers a variety of networking options to support a diverse set of applications and environments. Options include:

*  **Spot as a connected peer**. Applications can be deployed on computers that physically connect to Spot via the rear RJ-45 port, the DB-25 payload port, or the RJ-45 port on a Spot GXP payload. This provides a reliable, high-rate communications link without infrastructure requirements, but limits where the application can be run.
*  **Spot as a WiFi access point**. Applications with physical proximity to Spot can connect to the WiFi access point and communicate directly without any networking infrastructure.
*  **Spot as a WiFi client**. Spot can join an existing WiFi network, and applications can also join the same WiFi network to talk to Spot. This approach increases the possible range between application and Spot, but attention needs to be paid to dead zones in the network, handoff times between access points, and other considerations.
*  **Spot via custom communications links**. Custom communication links such as cell modems and Persistent Systems radios can act as a bridge between Spot and applications. These can be useful when the above cases are insufficient for network design.

While the application-layer protocol for the Spot API works across any IP-based network connection, the examples above show that networking choice can have a significant impact on the performance and reliability of an application as well as deployment strategies.

## gRPC and Protocol Buffers

[gRPC](https://grpc.io) is the application-level protocol used by the majority of the Spot API. gRPC was chosen because it provides a secure, performant protocol with support for a broad set of programming languages and environments.

gRPC specifies the service interfaces and remote procedure calls (RPCs) supported by the service. For example, the Spot API has an authentication service with the following definition:

```protobuf
service AuthService {
    rpc GetAuthToken(GetAuthTokenRequest) returns (GetAuthTokenResponse) {}
}
```

The service interface's name is `AuthService`. It only supports a single RPC named `GetAuthToken`, which checks the passed in username and password and returns a session token if they are valid.

The input (GetAuthTokenRequest) and output (GetAuthTokenResponse) messages are [Protocol Buffer](https://developers.google.com/protocol-buffers/docs/overview) messages. Protocol Buffer messages have a compact wire representation, support backwards/forwards compatibility, and are implemented for a broad set of programming languages and environments.

Protocol Buffer messages are defined using a language independent format, with automatically generated serialization/deserialization bindings for languages. For example, the definition for `GetAuthTokenRequest` can be seen below (or in [auth.proto](../../protos/bosdyn/api/auth.proto)):

```protobuf
message GetAuthTokenRequest {
    // Common request header.
    RequestHeader header = 1;
    // Username to authenticate with. Must be set if password is set.
    string username = 2;
    // Password to authenticate with. Not necessary if token is set.
    string password = 3;
    // Token to authenticate with. Can be used in place of the password, to re-mint a token.
    string token = 4;
}
```

Although the `AuthService` example shows the common RPC paradigm of single request/single response, gRPC also supports more advanced RPC paradigms such as streaming requests, streaming responses, or full bidirectional streaming.  The Spot API uses some of the more advanced paradigms in select locations. For example, gRPC limits responses to 4MB by default, which is too small for large amounts of data, such as the complete GraphNav map. The GraphNav service's upload and download requests provides a streaming response RPC to work around this limitation.

## Using gRPC and Protocol Buffers


The Python library included in the SDK hides the use of gRPC and Protocol Buffers and provides a simpler abstraction. For example, the `AuthClient` class, which speaks to the `AuthService` interface described above, has a method called `auth` demonstrated below.

```python
    def auth(self, username, password, app_token=None, **kwargs):
        """Authenticate to the robot with a username/password combo.

        Args:
            username: username on the robot.
            password: password for the username on the robot.
            app_token: Deprecated.  Only include for robots with old software.
            kwargs: extra arguments for controlling RPC details.

        Returns:
            User token from the server as a string.

        Raises:
            InvalidLoginError: If username and/or password are not valid.
        """
        req = _build_auth_request(username, password, app_token)
        return self.call(self._stub.GetAuthToken, req, _token_from_response, _error_from_response,
                         **kwargs)
```


This method takes `username`, `password`, and `app_token` strings and generates a `GetAuthTokenRequest` message from those using `_build_auth_request`. The RPC is then sent to the `AuthService` and a `GetAuthTokenResponse` is received. If the authentication attempt is valid, the session token is returned to the caller of the auth function. If there were networking issues or the username/password combination was invalid, an exception is raised.

This layer of abstraction simplifies common use cases, but developers will occasionally need to interact with Protocol Buffer messages directly, even when using the Python library. For example, the `RobotState` message includes many nested sub-messages and detailed information. Rather than convert into primitive types or other data structures, developers need to directly operate on the protocol buffer itself. The message definition and comments in [protos/bosdyn/api/robot_state.proto](../../protos/bosdyn/api/robot_state.proto) are key to understanding what is included and how to interpret the data.

Developers who wish to support another language or environment are also able to build client libraries using the gRPC service definitions and Protocol Buffer message definitions. The Python client library may also be used as a reference implementation.

## Error Handling

Robust applications need to handle errors when communicating with the Spot API. There are three general classes of errors:

*  **Networking errors**. Examples: network timeouts, inability to reach Spot, or security issues. The workaround is typically networking configuration specific.
*  **Common RPC errors**. Examples: invalid input or internal server errors. Typically the root cause is buggy application code and the only workaround is to fix the bug.
*  **Specific RPC errors**. Examples: service specific errors based on the returned `Status` messages, such as a bad username/password combination for the `AuthService` above. Application code should handle these errors gracefully.

More detail can be seen in the `GetAuthTokenResponse` Protocol Buffer message below:

```protobuf
message GetAuthTokenResponse {
    ResponseHeader header = 1;
    enum Status{
        // STATUS_UNKNOWN should never be used. If used, an internal error has happened.
        STATUS_UNKNOWN = 0;

        // STATUS_OK indicates that authentication has succeeded. The |token| field will
        // be populated with a session token that can be used to authenticate the user.
        STATUS_OK = 1;

        // STATUS_INVALID_LOGIN indicates that authentication has failed since an invalid
        // username and/or password were provided.
        STATUS_INVALID_LOGIN = 2;

        // STATUS_INVALID_TOKEN indicates that authentication has failed since the |token|
        // provided in the request is invalid. Reasons for the token being invalid could be
        // because it has expired, because it is improperly formed, for the wrong robot, the
        // user that the token is for has changed a password, or many other reasons. Clients
        // should use username/password-based authentication when refreshing the token fails.
        STATUS_INVALID_TOKEN = 3;

        // STATUS_TEMPORARILY_LOCKED_OUT indicates that authentication has failed since
        // authentication for the user is temporarily locked out because of too many unsuccessful
        // attempts. Any new authentication attempts should be delayed so they may happen after
        // the lock out period ends.
        STATUS_TEMPORARILY_LOCKED_OUT = 4;

        // STATUS_INVALID_APPLICATION_TOKEN indicates that the |application_token| in the
        // request was invalid.
        STATUS_INVALID_APPLICATION_TOKEN = 5;

        // STATUS_EXPIRED_APPLICATION_TOKEN indicates that the |application_token| in the
        // request was valid, but has expired.
        STATUS_EXPIRED_APPLICATION_TOKEN = 6;
    }
    Status status = 2;

    // Token data. Only specified if status == STATUS_OK.
    string token = 3;
}
```

The networking errors are not defined in the message and happen lower in the gRPC stack. The Specific RPC errors are handled by the `Status` enum shown above. Throughout the API, the `Status` enum follows the pattern of 0 being undefined (due to how Protocol Buffers represent unset data), 1 representing an `OK` or success response, and 2+ representing error codes specific to the RPC. For example, `STATUS_TEMPORARILY_LOCKED_OUT` is used if there have been too many password attempts for a user and the account is locked out for a short period.

Common RPC errors such as invalid input are not directly shown above. A case of invalid input would be a `GetAuthTokenRequest` which includes no username or password at all, which indicates buggy client code rather than bad user input. Common RPC errors are shown in the `ResponseHeader` message below which all Spot API responses include:

```protobuf
/// Standard header attached to all GRPC responses from services.
message ResponseHeader {
    /// Echo-back the RequestHeader for timing information, etc....
    RequestHeader request_header = 1;

    /// Time that the request was received. The server clock is the time basis.
    google.protobuf.Timestamp request_received_timestamp = 2;

    /// Time that the response was received. The server clock is the time basis.
    google.protobuf.Timestamp response_timestamp = 3;

    /// Common errors, such as invalid input or internal server problems.
    /// If there is a common error, the rest of the response message outside of the
    /// ResponseHeader will be invalid.
    CommonError error = 4;

    /// Echoed request message. In some cases it may not be present, or it may be a stripped
    /// down representation of the request.
    google.protobuf.Any request = 5;
}
```

The Python library handles Networking, Common RPC errors, and Specific RPC errors by raising specific Exceptions, which application developers can accept.

## HTTP/2, TLS, and TCP

gRPC is built on top of other networking protocols, as shown in the diagram below.

<img src="network_protocol_stack.png" alt="Network protocol stack" style="width:350px">

This protocol stack has a few implications:

*  HTTP/2 supports multiplexing multiple gRPC calls over the same network connection. Responses can come back in a different order than received, and a low priority response can be interrupted by a higher priority response and then resumed later. gRPC requests map directly to HTTP/2 requests.
*  All communication is over a secure, encrypted TLS channel (TLS1.2 or TLS1.3 are supported). Network attackers can not read or manipulate data between the application and Spot. Client libraries should also verify that the certificate presented by a server chains up to a Boston Dynamics root certificate to prevent active MITM attacks. The Python client library automatically does this certificate verification approach.
*  Communication is over a reliable transport layer with TCP. Reliable transport is a good approach for non-real-time RPCs such as authenticating to Spot, and is also not problematic for real-time cases where there is a strong networking link such as through the RJ45 or DB-25 connectors. However, it can be problematic when handling real-time RPCs over a spotty network connection. There are some short-term mitigation approaches around this such as maintaining a socket pool to round-robin requests over. In the longer term, Boston Dynamics is exploring other approaches (such as gRPC over QUIC or HTTP/3) to improve communications over poor network links.
*  The protocol stack is a very common one for the Internet at large. This has two benefits. First, Spot is able to use battle-tested implementations of the protocols which can withstand adversarial attackers. Second, there is a very high likelihood that an application can reach Spot over a diverse set of networks without being blocked by intermediate firewalls.

## Robot Discovery

To talk to Spot, a client application needs to specify an IP address where a Spot is running. There are a number of possible options for doing this sort of robot discovery.

*  **Fixed IP address**. This approach can be used reliably when connecting directly to Spot as a WiFi access point, or over ethernet. No name lookup infrastructure is required.
*  **DNS name**. A DNS server (or HOSTS file) can be configured to statically point to a fixed IP address that Spot listens on, and the application specifies a DNS name to reach.
*  **mDNS discovery**. Spot will send mDNS/DNS-SD broadcasts starting with the Spot 2.0 release. Clients on the same network can listen for these packets and discover robots that are available via the announcements.
*  **Custom Discovery mechanism**. Applications can develop custom approaches to map a specific Spot to an IP address, such as using a cloud-based discovery endpoint.

Client applications do not use the symbolic name of the robot (if any) when verifying the certificate during the TLS handshake to the robot. This supports a variety of discovery mechanisms without requiring new certificates to be provisioned.
