<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Data Acquisition Output

 The data stored from data acquisition captures can be downloaded over a REST endpoint from the robot. When downloading the data, the result will be returned in a zip file containing all data that matches the particular query parameters sent to the endpoint.

## Zip file structure

An example zip file with data from both a teleoperation session and a run of a mission named "Inspection":
```
downloaded_file.zip
└───teleop_2020-10-29T183020Z
│   │   metadata.json
│   │   basic-position-data.csv
│   │   detailed-position-data.csv
│   │   SpotCAM All 1 spot-cam-pano.jpg
│   │   SpotCAM All 1 spot-cam-ptz.jpg
│   │   SpotCAM ir nodata 2 spot-cam-ir.jpg
│       ...
└───2020-10-29T185610Z_Inspection
    │   metadata.json
    │   basic-position-data.csv
    │   detailed-position-data.csv
    │   SpotCAM All 1 spot-cam-pano.jpg
    │   SpotCAM All 1 spot-cam-ptz.jpg
    │   SpotCAM ir nodata 2 spot-cam-ir.jpg
        ...
```


Each separate group from the stored data will be in its own directory. The directory name will be the `group_name`, formatted as `<mission start timestamp>_<mission name>` for Autowalk missions, or `teleop_<session start timestamp>` for teleop captures.

Within each group's directory the images captured as part of that group will be saved with filenames of the form `<action name> <image service name>-<image source name>.jpg`. There will be a `metadata.json` file with all of the associated metadata captured during that group, and optionally CSV files for basic or detailed position data (present if the data was captured during the group's actions).

## Metadata.json structure

The json data is structured around actions, and the data within those actions. Metadata is included either nested with the data it is associated with, or nested inside the action it was captured during.

```javascript
{
  "actions": [
    {
      // Identifier including the action name and timestamp.
      "action_id": {},
      // data captured during this action
      "data": {},
      // metadata associated with this action, but not any particular
      // piece of data.
      "metadata": {}
    },
    {
      "action_id": {},
      "data": {},
      "metadata": {}
    },
  ]
}
```
The "data" member will contain entries that map to the files stored in the zip, while the "metadata" member will contain json data that is associated with the action.
Within the "data" or "metadata" members of an action, the individual entries will be stored in a list inside a member with the name of the channel. In general there will only be a single element inside this list, unless you separately store multiple pieces of data or metadata to the same channel during a particular capture action.
Any json saved as part of the `metadata` field in `AcquireDataRequest` or the `metadata` argument to `DataAcquisitionClient.acquire_data()` will be saved on the "metadata" channel. Autowalk action tags are stored in this manner in a "custom_metadata" member.

Note that these pieces of data or metadata can have their own set of "metadata", with the same format as the metadata for an action, for pieces of metadata that referenced them explicitly. For example, capturing GPS coordinates would reference the entire action, but computing bounding boxes in an image would reference that particular image only.

```javascript
{ // beginning of an action in the "actions" list.
  "action_id": {},
  "data":{
    "some_image_channel": [
      {
        // Identifier for this image capture.
        "data_id": {},
        // Relative path to the image file.
        "filename": "...",
        // metadata associated with this particular image
        "metadata": {}
      }
    ],
    "another_channel": [
      {
        "data_id": {},
        "filename": "..."
      }
    ]
  },
  "metadata":{
    "basic-position-data": [
      {
        // Identifier for this basic-position-data capture.
        "data_id": {},
        // json representation of the data captured.
        "data": "...",
        // More metadata added later that refers to this particular metadata information.
        "metadata": {}
      }
    ],
    "my_metadata_channel": [
      {
        "data_id": {},
        "data": "...",
        "metadata": {}
      }
    ]
  }
}
```

Data from an example mission:
```javascript
{
  "actions": [
    {// First capture action
      "action_id": {
        "timestamp": "2020-10-29T18:56:27.786897121Z",
        "group_name": "2020-10-29T185610Z_Inspection",
        "action_name": "SpotCAM All 1"
      },
    "data": { // Two images were captured at this action
      // One panoramic image on the "spot-cam-pano" channel
      "spot-cam-pano": [
        {
          "data_id": {
            "action_id": {
              "timestamp": "2020-10-29T18:56:27.786897121Z",
              "group_name": "2020-10-29T185610Z_Inspection",
              "action_name": "SpotCAM All 1"
            },
            "channel": "spot-cam-pano",
            // data_name is usually left empty like this.  It is used to differentiate captures
            // on the same channel at the same action, if needed.
            "data_name": ""
          },
          // filename is relative to this metadata.json file.
          "filename": "SpotCAM All 1 spot-cam-pano.jpg"
        }
      ],
      // One PTZ image on the "spot-cam-ptz" channel
      "spot-cam-ptz": [
        {
          "data_id": {
            "action_id": {
              "timestamp": "2020-10-29T18:56:27.786897121Z",
              "group_name": "2020-10-29T185610Z_Inspection",
              "action_name": "SpotCAM All 1"
            },
            "channel": "spot-cam-ptz",
            "data_name": ""
          },
          "filename": "SpotCAM All 1 spot-cam-ptz.jpg"
        }
      ]
    },
    // Metadata associated with the action itself, rather than a particular image.
    "metadata": {
      // Robot localization data saved on the "detailed-position-data" channel.
      "detailed-position-data": [
        {
          "data_id": {
            "action_id": {
              "timestamp": "2020-10-29T18:56:27.786897121Z",
              "group_name": "2020-10-29T185610Z_Inspection",
              "action_name": "SpotCAM All 1"
            },
          "channel": "detailed-position-data",
          "data_name": ""
        },
      "data": {
        "robot_kinematics": {
          "velocity_of_body_in_vision": {
            "angular": {
              "x": -0.0012627621181309223,
      ...
      ],
      // Autowalk tags saved on the "metadata" channel.
      "metadata": [
        {
          "data_id": {
            "action_id": {
              "timestamp": "2020-10-29T18:56:27.786897121Z",
              "group_name": "2020-10-29T185610Z",
              "action_name": "SpotCAM All 1"
            },
            "channel": "metadata",
            "data_name": ""
          },
          "data": {
            "custom_metadata": [
              "laptop1"
            ]
          }
        }
      ],
      ...
```
## CSV structure

The csv files will have one row for every file in the group. The columns of the csv file will be a flattened version of the basic-position-data or detailed-position-data metadata, as well as any custom Autowalk tags entered during recording.

Entries will be left empty in a row if the data was not captured for that file.