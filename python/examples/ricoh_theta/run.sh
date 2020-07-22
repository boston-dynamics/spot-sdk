#!/bin/bash

# Edit the path to the python script if required
# This remote_mission_service_ricoh example utilizes the limited-access user token availble from payload self-registration
python3 /home/spot/ricoh_theta/remote_mission_service_ricoh.py 192.168.50.3 --payload-token --directory-host 192.168.50.3 --my-host 192.168.50.5 --theta-client


