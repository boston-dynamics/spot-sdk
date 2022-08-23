<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Cloud Upload Example

The cloud_upload.py script shows how to upload a file to a Google Cloud Platform (GCP) bucket or an Amazon Web Services (AWS) S3 bucket.

The two functions below are defined in the cloud_upload.py script:

```python
def upload_to_gcp(bucket_name, source_file, destination_file):
def upload_to_aws(bucket_name, source_file, destination_file):
```

They both take the same arguments:

```
        bucket_name = "your-bucket-name"
        source_file = "local/path/to/file"
        destination_file = "storage-object-name"
```

Credentials are stored in a file. For GCP, the user needs to set an environment variable; for AWS, the credentials are hard coded. See below for details.

## Install Packages

Two python packages will need to be installed:

- google-cloud-storage
- boto3

```
python3 -m pip install -r requirements.txt
```

## Credentials

Each cloud service requires credentials to be properly setup.

### GCP

For the GCP, the user needs to point to the service account .json file with an environmental variable. Here is an example of how to do that with linux:

```
export GOOGLE_APPLICATION_CREDENTIALS=<path-to-file>/<filename>.json
```

Add the above line to your .bashrc file to make permanent. More information (including a Windows example) can be found [here](https://cloud.google.com/docs/authentication/production#linux-or-macos).

### AWS

For AWS, the user must have the default user credentials file stored in ~/.aws/credentials. More information can be found [here](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html).

## Running the Example

If the cloud credentials have been properly setup, the `main()` function in cloud_upload.py is currently configured to upload `requirements.txt` to an AWS S3 bucket (simply change `upload_to_aws` to `upload_to_gcp` to use a GCP bucket instead). A snippet of cloud_upload.py is included below.

```python
aws_bucket_name = 'aws-imagedemo' # s3 bucket name
source_file = 'requirements.txt' # sample file to upload
destination_file = source_file # using source_file name as destination_file name
upload_to_aws(aws_bucket_name, source_file, destination_file)
```

Run the example script by executing this command in your CLI.

```
python3 cloud_upload.py
```

The user should see the below response for a successful AWS upload.

```
Found credentials in shared credentials file: ~/.aws/credentials (credentials.py:1196)
Upload of file requirements.txt as requirements.txt to aws-imagedemo successful (cloud_upload.py:45)
```

And this response for a successful GCP upload.

```
Upload of file requirements.txt as requirements.txt to c-imagedemo successful (cloud_upload.py:26)
```

## Autowalk Example

An example of how to utilize these functions in a remote_mission_service application can be found in the [ricoh_theta](../ricoh_theta/README.md) example.
