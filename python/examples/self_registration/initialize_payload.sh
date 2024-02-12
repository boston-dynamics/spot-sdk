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
# payload_credentials_file - A file where the GUID and Secret for this instance are written

# Compile the protobuf files.
python3 -m pip install grpcio-tools
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. announce.proto announce_service.proto

# Robot definition:
# All requests will be routed to the robot IP.
robot_ip="$1"

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

# On the initial registration we will generate a payload credentials file containing a
# per-instance GUID and secret. This can be reused by future services by simply pointing
# to the file. If the file is already populated from a previous registration of this
# payload, we will reuse those values.
python3 self_register_payload.py --payload-credentials-file "$4" --name "$payload_name" \
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
python3 self_register_service.py --payload-credentials-file "$4" \
    --host-ip $endpoint_ip --port $endpoint_port $robot_ip
if [ $? -ne 0 ]; then
    kill -9 $announce_service_script_pid
    exit
fi
echo "Announce service registration complete."

# Create a client and access the Announce Service through the robot.
sleep 5 # Give the robot time to initialize the service
python3 announce_client.py --payload-credentials-file "$4" \
    --message "This message is passed through the robot." $robot_ip
if [ $? -ne 0 ]; then
    kill -9 $announce_service_script_pid
    exit
fi

# Cleanup background process.
kill -9 $announce_service_script_pid
echo "Payload and service initialization run complete."
