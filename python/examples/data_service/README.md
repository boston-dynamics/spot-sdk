<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Using the Robot Data Service

The data service tracks data logged to the robot via the API.  This includes:
- Text messages: Info/Warning/Error/Debug messages, typically logged by API services.
- Comments: Short messages, typically added by operators about the robot behavior.
- Events: Messages documenting a robot or client event, with a timestamp and possibly a duration.
- Message blobs: Arbitrary binary message blobs.

These, and other, messages are stored in data "pages" on the robot. A page is a discrete unit of storage tracked by the data service.

These example programs demonstrate how to query the robot data service for information about the robot's data pages and their contents.

## Setup Dependencies
This example requires the bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:
```
python3 -m pip install -r requirements.txt
```

## Running the Examples
Each example requires that you specify a username and password to authenticate with the robot.

### get_comments.py
Get operator comments logged via API.
```
python3 get_comments.py --username USER --password PASSWORD ROBOT_IP
```

### get_events.py
Get events logged on the robot.
```
python3 get_events.py --username USER --password PASSWORD ROBOT_IP
```

### get_index.py
Get lists of pages that contain blobs, text-message, events, or operator comments. COMMAND may be one of blob, text, event, or comment.
```
python3 get_index.py --username USER --password PASSWORD ROBOT_IP COMMAND
```

### get_pages.py
Get a list of data pages currently on the robot.
```
python3 get_pages.py --username USER --password PASSWORD ROBOT_IP
```

You may optionally specify a time range of pages to return. Times are specified in RFC3339 format. For example:
```
python3 get_pages.py --username USER --password PASSWORD --start 2020-10-01T00:00:01Z --end 2020-10-31T11:59:59Z ROBOT_IP
```
You may specify only one start or only end time if preferred.

### delete_pages.py
Delete data pages from the robot. Running this without a time range will delete all data pages on the robot.
```
python3 delete_pages.py --username USER --password PASSWORD ROBOT_IP
```
You may optionally specify a time range of pages to delete. Times are specified in RFC3339 format. For example:
```
python3 get_pages.py --username USER --password PASSWORD --start 2020-10-01T00:00:01Z --end 2020-10-31T11:59:59Z ROBOT_IP
```
You may specify only one start or only end time if preferred.
