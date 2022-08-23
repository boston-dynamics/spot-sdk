<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Using the Robot Data Service

The data service tracks data logged to the robot via the API. This includes:

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
python3 get_comments.py ROBOT_IP
```

### get_events.py

Get events logged on the robot.

```
python3 get_events.py ROBOT_IP
```

### get_index.py

Get lists of pages that contain blobs, text-message, events, or operator comments. COMMAND may be one of blob, text, event, or comment.

```
python3 get_index.py ROBOT_IP COMMAND
```

### get_pages.py

Get a list of data pages currently on the robot.

```
python3 get_pages.py ROBOT_IP
```

You may optionally specify a time range of pages to return.

For example:

```
python3 get_pages.py \
    --timespan 20201030-20201031 ROBOT_IP
```

See the description of time range specifications below.

### delete_pages.py

Delete data pages from the robot. Running this without a time range will delete all data pages on the robot.

```
python3 delete_pages.py ROBOT_IP
```

You may optionally specify a time range of pages to delete. For example:

```
python3 delete_pages.py \
    --timespan 20201031_115000-20201031_115950 --robot-time ROBOT_IP
```

You may specify only one start or only end time if preferred.

### Time ranges

Times in the command-line arguments are of the format _val_or \_val_-_val_ where _val_ has one of these formats:

- _yyyymmdd_hhmmss_ (e.g., `20200120_120000`)
- _yyyymmdd_ (e.g., `20200120`)
- *n*d _n_ days ago
- *n*h _n_ hours ago
- *n*m _n_ minutes ago
- *n*s _n_ seconds ago
- _nnnnnnnnnn[.nn]_ (e.g., `1581869515.256`) Seconds since epoch
- _nnnnnnnnnnnnnnnnnnnn_ Nanoseconds since epoch

So:

- `5m` means from 5 minutes ago until now.
- `20201107-20201108` means all of 2020/11/07.

Adding `--robot-time` indicates that the specified time range is in the robot clock, so the specified value should _not_ be converted from client time to robot time.
