#!/bin/bash
ROBOT_IP=192.168.50.3
USERNAME=
PASSWORD=
PAYLOAD_CRED_PATH=/opt/payload_credentials/payload_guid_and_secret
PORT=50055

# Load the docker image
sudo docker load -i fireextinguisherserver.tar
# Start the server with robot username and password
# sudo docker run -d --name retinanet_server --network host --restart unless-stopped -v $PAYLOAD_CRED_PATH:$PAYLOAD_CRED_PATH fireextinguisherserver -d . --username $USERNAME --password $PASSWORD $ROBOT_IP
# Start the server with spotcore credentials
sudo docker run -d --name retinanet_server --network host --restart unless-stopped --mount "type=bind,$PAYLOAD_CRED_PATH,$PAYLOAD_CRED_PATH,readonly" fireextinguisherserver -d . -port $PORT $ROBOT_IP --payload-credentials-file $PAYLOAD_CRED_PATH
