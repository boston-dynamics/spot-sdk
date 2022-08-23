#!/bin/bash
#
# This script will:
# 0. Compile the Announce protobuf files
# 1. Register the payload (current system) with a robot
# 2. Register the Announce Service with a robot
# 3. Start an instance of Announce Service on the current system
# 4. Create a client and access the Announce Service through the robot

# Arguments:
# <robot_ip> <endpoint_ip> <endpoint_port> <payload_secret>
# robot_ip - IP address the robot can be accessed at from the current system
# endpoint_ip - IP address the current system can be accessed at from the robot
# endpoint_port - An open port on the current system for the service to communicate through
# payload_secret - A private 16 character string unique to this payload instance

# Compile the protobuf files.
python3 -m pip install grpcio-tools
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. announce.proto announce_service.proto

# Robot definition:
# All requests will be routed to the robot IP.
robot_ip="$1"

# Payload definition:
# GUID should be a uniquely generated GUID.
payload_guid="f71966ec-5c0e-43c1-92d6-522f12736fe9"
# Secret should be an arbitrary string. Human readability is not necessary.
payload_secret="$4"
# Name is a human-readable string used to identify a payload.
payload_name="Self-Registered-Payload"
# Description is human-readable explanation of a payload.
payload_description="This payload registered itself via the $(basename -- "$0") example."

# Endpoint definition:
# The endpoint defines the network location that the payload service can be reached at.
# It must be accessible from the robot - on the same subnet and not blocked by a firewall.
# IP address of the system running the service.
endpoint_ip="$2"
# A free port on the system to access to the service through.
endpoint_port="$3"

# Register the payload. Only need to register a single time.
python3 self_register_payload.py --guid "$payload_guid" --secret "$payload_secret" --name "$payload_name" \
    --description "$payload_description" $robot_ip
if [ $? -ne 0 ]; then exit; fi
echo "Payload registration complete."

# Start the Announce Service on this system.
python3 announce_service.py --port $endpoint_port &
announce_service_script_pid=$!
if [ $? -ne 0 ]; then
    kill -9 $announce_service_script_pid
    exit
fi
echo "Announce service started."

# Register the service. This can be called from the payload or an arbitrary API client.
# Must be registered after each robot power cycle.
python3 self_register_service.py --guid $payload_guid --secret "$payload_secret" \
    --host-ip $endpoint_ip --port $endpoint_port $robot_ip
if [ $? -ne 0 ]; then
    kill -9 $announce_service_script_pid
    exit
fi
echo "Announce service registration complete."

# Create a client and access the Announce Service through the robot.
sleep 5 # Give the robot time to initialize the service
python3 announce_client.py --guid $payload_guid \
    --secret "$payload_secret" \
    --message "This message is passed through the robot." $robot_ip
if [ $? -ne 0 ]; then
    kill -9 $announce_service_script_pid
    exit
fi

# Cleanup background process.
kill -9 $announce_service_script_pid
echo "Payload and service initialization run complete."
