# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
An example to show how to export SiteWalk archives from Orbit to the ./temp folder in the current directory
"""

import argparse
import logging
import os
import sys

from bosdyn.orbit.client import create_client
from bosdyn.orbit.utils import add_base_arguments

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
log_format = "Export SiteWalk Archives: %(levelname)s - %(message)s"
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter(log_format))
LOGGER.addHandler(ch)

DOWNLOAD_ALL_CMD = 'all'


def export_site_walk_archive(options: argparse.Namespace) -> bool:
    """ A simple example to show how to use the Orbit client to export SiteWalk archives
        which represent a collection of graph and mission data from Orbit.

        Args:
            options(Namespace) : parsed args used for configuration options
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedClientError: indicates that the orbit client is not authenticated properly
        Returns
            Boolean to indicate whether the function succeeded or not
    """

    # Create Orbit client object
    orbit_client = create_client(options)

    # Retrieve a collection of all SiteWalks stored on Orbit
    get_site_walks_response = orbit_client.get_site_walks()

    # Check that the get_site_walks_archive_response is valid
    if not get_site_walks_response.ok:
        LOGGER.error(
            "Access error to site_walks/archive endpoint. Please make sure you are using an admin account!"
            + get_site_walks_response.reason)
        return False

    # Obtain the json form of the response
    site_walks_json = get_site_walks_response.json()

    # Create a temp directory to store the SiteWalk Archives
    if not (os.path.exists('temp')):
        os.makedirs('temp')

    LOGGER.info(
        "There are {} site_walks available to export SiteWalk archives in the form of ZIP:\n".
        format(len(site_walks_json)))

    # Display the SiteWalks available to download
    available_site_walks = []

    for site_walk in site_walks_json:
        print(str(site_walks_json.index(site_walk) + 1) + ". " + str(site_walk['name']))

        # Store the name and uuid of each SiteWalk in a list of available SiteWalks to download
        available_site_walks.append({"name": site_walk['name'], "uuid": site_walk['uuid']})

    valid_selection = False
    site_walk_selected_indices = ''

    while not valid_selection:
        # Prompt the user to select a SiteWalk by index or backup all SiteWalks with DOWNLOAD_ALL_CMD
        site_walk_selected_indices = input(
            "\nSelect SiteWalks to export archives by providing the associated index. For exporting multiple indices, please list them in a comma-separated format. If the indices are 1, 2, 3, and 4, you should enter them as 1, 2, 3, 4. To export all indices, simply type 'all'. \n> "
        )

        # If user types DOWNLOAD_ALL_CMD create a list including all of the indices of available SiteWalks
        if site_walk_selected_indices.lower() == DOWNLOAD_ALL_CMD:
            site_walk_selected_indices = range(len(available_site_walks) - 1)
            valid_selection = True
        # Parse comma separated indices user input
        else:
            try:
                # Try separating the user input selected indices of SiteWalks by comma
                site_walk_selected_indices = site_walk_selected_indices.split(',')
                valid_selection = True

                for i in range(len(site_walk_selected_indices)):
                    site_walk_selected_indices[i] = int(site_walk_selected_indices[i])

                    # Check if all selected indices are in the range of its Walk indices listed from above
                    if site_walk_selected_indices[i] > len(
                            available_site_walks) + 1 or site_walk_selected_indices[i] < 0:
                        invalid_index = site_walk_selected_indices[i]
                        LOGGER.error(
                            f"Invalid Index Selection - Index {invalid_index} is out of range of available SiteWalk indices listed above. Please type a valid selection of SiteWalk indices from the list above or type {DOWNLOAD_ALL_CMD}"
                        )
                        valid_selection = False
                        break

            except:
                LOGGER.error(
                    f"Please type a valid selection of SiteWalk indices from the list above or type {DOWNLOAD_ALL_CMD}"
                )
                valid_selection = False

    # Create a list of selected SiteWalks after parsing user input
    selected_site_walks = []

    for selected_index in site_walk_selected_indices:
        if selected_index < len(available_site_walks) + 1 and selected_index > 0:
            selected_site_walks.append(available_site_walks[selected_index - 1])

    # Download the SiteWalks archives to the ./temp folder
    for site_walk in selected_site_walks:
        # Get the SiteWalk Archive using it's uuid
        get_site_walk_archive_by_id_response = orbit_client.get_site_walk_archive_by_id(
            site_walk['uuid'])

        # Check that the get_site_walk_archive_by_id_response is valid
        if not get_site_walk_archive_by_id_response.ok:
            LOGGER.error("Get SiteWalks archives response error " +
                         get_site_walk_archive_by_id_response.reason)
            return False

        # Obtain the content field containing the zip file
        site_walk_archive_zip_file = get_site_walk_archive_by_id_response.content

        # Set the file name to the SiteWalk name to be downloaded
        site_walk_name = site_walk['name']

        file_name = f'temp/{site_walk_name}.walk.zip'

        # Write the site_walk_archive_zip_file to file_name
        with open(file_name, "wb") as file:
            file.write(site_walk_archive_zip_file)

        LOGGER.info("Downloaded: " + file_name)

    return True


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    add_base_arguments(parser)
    options = parser.parse_args()

    export_site_walk_archive(options)


if __name__ == '__main__':
    if not main():
        sys.exit(1)
