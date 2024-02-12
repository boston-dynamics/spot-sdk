<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Extract Images from Walk File Example

This example extracts all images from a v3.3+ autowalk mission ".walk" file and puts them in a pptx slideshow with action name and capture type.
Each image is on a slide which shows:

- Action name
- Image source
- Minimum and maximum frequencies for acoustic inspection actions
- Network compute capture information if applicable

It also saves all the images as jpegs with a filename corresponding to their action name.

## Setup Dependencies

These examples need to be run with python3, and have the Spot SDK installed. See the requirements.txt file for a list of dependencies which can be installed with pip.

```
$ python3 -m pip install -r requirements.txt
```

## Run the Example

To run the example:

```
python3 extract_images_from_walk.py --input_file PATH_TO_WALK_FILE --output_directory DIRECTORY_FOR_OUTPUT
```

### Arguments

`--input_file` Path to the .walk file to extract images from
`--output_directory` (optional) Path to the directory to output to, default is current directory
