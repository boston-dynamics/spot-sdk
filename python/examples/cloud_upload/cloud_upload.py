# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Upload files to cloud example"""
import logging
import sys

import boto3  # Import for AWS
from google.cloud import storage  # Import for GCP

logger = logging.getLogger(__name__)


def upload_to_gcp(bucket_name, source_file, destination_file):
    """Uploads a file to your GCP Bucket.

    Args:
        bucket_name (str): "your-bucket-name"
        source_file (str): "local/path/to/file"
        destination_file (str): "storage-object-name"

    Credentials:
        Must have service account json as environmental variable.
        Linux Ex: export GOOGLE_APPLICATION_CREDENTIALS=<path-to-file>/<filename>.json
        https://cloud.google.com/docs/authentication/production#linux-or-macos
    """

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_file)
    blob.upload_from_filename(source_file)
    logger.info('Upload of file {} as {} to {} successful'.format(source_file, destination_file,
                                                                  bucket_name))


def upload_to_aws(bucket_name, source_file, destination_file):
    """Uploads a file to your AWS s3 bucket.

    Args:
        bucket_name (str): "your-bucket-name"
        source_file (str): "local/path/to/file"
        destination_file (str): "storage-object-name"

    Credentials:
        Must have default user credentials in ~/.aws/credentials.
        https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html
    """

    s3 = boto3.client('s3')
    s3.upload_file(source_file, bucket_name, destination_file)
    logger.info('Upload of file {} as {} to {} successful'.format(source_file, destination_file,
                                                                  bucket_name))


def main(argv):
    """Upload to AWS Example"""

    # Setting up logger for informational print statements.
    global logger
    level = logging.INFO  # use logging.DEBUG for verbose details
    logging.basicConfig(level=level, format='%(message)s (%(filename)s:%(lineno)d)')
    logger = logging.getLogger()

    # Adjust the below parameters for your specific use case.
    # Optionally: Each of these parameters could also be set using argparse.
    aws_bucket_name = 'aws-imagedemo'  # s3 bucket name
    source_file = 'requirements.txt'  # test file to upload
    destination_file = source_file  # using source_file name as destination_file name
    upload_to_aws(aws_bucket_name, source_file, destination_file)


if __name__ == '__main__':
    main(sys.argv[1:])
