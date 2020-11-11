# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import io
import os
import json

from bosdyn.api import image_pb2
from bosdyn.client.exceptions import ResponseError

from google.protobuf import json_format

def clean_filename(filename):
    """Removes bad characters in a filename.

    Args:
        filename(string): Original filename to clean.

    Returns:
        Valid filename with removed characters :*?<>|
    """

    return "".join(i for i in filename if i not in ":*?<>|")


def download_data_REST(query_params, hostname, token, destination_folder='.',
    additional_params=None):
    """Retrieve all data for a query from the DataBuffer REST API and write it to files.

    Args:
        query_params(bosdyn.api.DataQueryParams): Query parameters to use to retrieve metadata from
            the DataStore service.
        hostname(string): Hostname to specify in URL where the DataBuffer service is running.
        token(string): User token to specify in https GET request for authentication.
        destination_folder(string): Folder where to download the data.
        additional_params(dict): Additional GET parameters to append to the URL.

    Returns:
        Boolean indicating if the data was downloaded successfully or not.
    """
    import requests
    try:
        url = 'https://{}/v1/data-buffer/daq-data/'.format(hostname)
        folder = clean_filename(os.path.join(destination_folder, 'REST'))
        if not os.path.exists(folder):
            os.mkdir(folder)
        headers = {"Authorization": "Bearer {}".format(token)}
        get_params = additional_params or {}
        if query_params.HasField('time_range'):
            get_params.update({'from_nsec': query_params.time_range.from_timestamp.ToNanoseconds(),
                'to_nsec': query_params.time_range.to_timestamp.ToNanoseconds()})
        chunk_size = 10 * (1024 ** 2) # This value is not guaranteed.

        with requests.get(url, verify=False, stream=True, headers=headers,
            params=get_params) as resp:
            print("Download request HTTPS status code: %s" % resp.status_code)
            # This is the default file name used to download data, updated from response.
            if resp.status_code == 204:
                print("No content avaialble for the specified download time range (in seconds): "
                "[%d, %d]"% (query_params.time_range.from_timestamp.ToNanoseconds()/1.0e9,
                query_params.time_range.to_timestamp.ToNanoseconds()/1.0e9))
                return False
            download_file = os.path.join(folder, "download.zip")
            content = resp.headers['Content-Disposition']
            if len(content) < 2:
                print("ERROR: Content-Disposition is not set correctly")
                return False
            else:
                start_ind = content.find('\"')
                if start_ind == -1:
                    print("ERROR: Content-Disposition does not have a \"")
                    return False
                else:
                    start_ind += 1
                    download_file = os.path.join(folder, content[start_ind:-1])

            with open(download_file, 'wb') as fid:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    print('.', end = '', flush=True)
                    fid.write(chunk)
    except requests.exceptions.HTTPError as rest_error:
        print("REST Exception:\n")
        print(rest_error)
        return False
    except IOError as io_error:
        print("IO Exception:\n")
        print(io_error)
        return False

    # Data downloaded and saved to local disc successfully.
    return True
