# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use the Orbit client to create Orbit backups through the Boston Dynamics Orbit API."""
import argparse
import datetime
import logging
import sys
import time

from bosdyn.orbit.client import Client, create_client
from bosdyn.orbit.utils import add_base_arguments, print_json_response

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
log_format = "Orbit Backups: %(levelname)s - %(message)s"
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter(log_format))
LOGGER.addHandler(ch)


def start_backup(orbit_client: Client, include_missions: bool, include_captures: bool) -> str:
    """ A simple example to show how to use the Orbit client to start the backup process.

        Args: 
            include_missions: Specifies whether to include missions and maps in the backup.
            include_captures: Specifies whether to include all inspection data captures in the backup.
        Returns:
            String of the task ID for that backup.
    """
    # Start the backup process
    response = orbit_client.post_backup_task(include_missions, include_captures)
    # If the response is okay, get the task ID
    if print_json_response(response):
        response_json = response.json()
        # Get the backup task from the response to obtain the task ID
        if response_json.get("data"):
            backup_task = response_json.get("data")
            task_id = backup_task.get("taskId")
            return task_id
        else:
            LOGGER.error("No backup task found in the response!")
    return None


def get_backup_task_status(orbit_client: Client, task_id: str) -> tuple[str, str]:
    """Retrieves the backup status including errors for a given task ID.

        Args:
            task_id (str): The ID of the task.
        Returns:
            tuple: A tuple containing the status and errors. The status represents the backup status, and the errors represent any errors encountered during the backup process.
    """
    response = orbit_client.get_backup_task(task_id)
    # If the response is okay, get the task status and errors
    if print_json_response(response):
        response_json = response.json()
        status = response_json.get("status")
        errors = response_json.get("error")
        return status, errors
    return None, None


def download_backup_file(orbit_client: Client, task_id: str, file_path: str):
    """ Retrieves a backup file for a given task ID and saves it to the specified file path.

        Args:
            task_id (str): The ID of the task for which the backup file is requested.
            file_path (str): The path where the backup file will be saved.
    """
    response = orbit_client.get_backup(task_id)
    # If the response is okay, get the backup file
    if response.ok:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        LOGGER.info(f"Full backup content saved to {file_path}")


def delete_backup(orbit_client: Client, task_id: str):
    """Deletes a backup with the specified task ID.

        Args:
            task_id (str): The ID of the backup task to delete.
    """
    response = orbit_client.delete_backup(task_id)
    print_json_response(response)


def get_backup(orbit_client: Client, file_path: str, include_missions: bool,
               include_captures: bool):
    """Initiates the backup process and downloads the backup file.

        Args:
            file_path: The path where the backup file will be saved.
            include_missions: Flag indicating whether to include missions in the backup.
            include_captures: Flag indicating whether to include captures in the backup.
        Returns:
            bool: True if the backup process is completed successfully, False otherwise.
    """

    # Start the backup process
    task_id = start_backup(orbit_client=orbit_client, include_missions=include_missions,
                           include_captures=include_captures)
    # If the task ID is not None, keep checking the status until the backup is completed
    if task_id:
        status, errors = get_backup_task_status(orbit_client=orbit_client, task_id=task_id)
        # Keep getting the status until there are errors or it is completed
        while status not in ["Completed", "Cancelled"] and not errors:
            status, errors = get_backup_task_status(orbit_client=orbit_client, task_id=task_id)
            # If the status is completed, download the backup file
            time.sleep(10)
        if status == "Completed":
            download_backup_file(orbit_client=orbit_client, task_id=task_id, file_path=file_path)
            return True
    else:
        LOGGER.error("Unable to start backup")
    return False


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    add_base_arguments(parser)
    parser.add_argument('--file-path',
                        help='Full path to where the tar file should be saved on your disk.',
                        default=None, required=False, type=str)
    parser.add_argument('--include-missions',
                        help='Specifies whether to include missions and maps in the backup.',
                        action='store_true')
    parser.add_argument(
        '--include-captures',
        help='Specifies whether to include all inspection data captures in the backup.',
        action='store_true')
    options = parser.parse_args()
    file_path = options.file_path
    # If a file path was not provided the backup will be in the current directory with a file named by the date
    if not file_path:
        currTime = datetime.datetime.now()
        formatted_date = currTime.strftime('%m_%d_%Y_%H_%M')
        file_path = f'backup_from_{formatted_date}.tar'

    # Create an orbit client
    orbit_client = create_client(options)

    # Start the backup process
    get_backup(orbit_client=orbit_client, file_path=file_path,
               include_missions=options.include_missions, include_captures=options.include_captures)


if __name__ == '__main__':
    if not main():
        sys.exit(1)
