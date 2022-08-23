# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""pyqt wrapper for bddf_download.py"""

import argparse
import datetime
import logging
import os
import platform
import signal
import subprocess
import sys

from bddf_download import collect_and_write_file, prepare_download
from PyQt5 import QtCore, QtWidgets, uic

import bosdyn.client
from bosdyn.api.data_index_pb2 import EventsCommentsSpec
from bosdyn.client.data_service import DataServiceClient
from bosdyn.client.time_sync import TimeSyncClient, TimeSyncEndpoint
from bosdyn.util import duration_str

# Use for PyInstaller Executable.
QTCREATORFILE = 'download.ui'
if hasattr(sys, '_MEIPASS'):
    UI_PATH = os.path.join(sys._MEIPASS, QTCREATORFILE)
else:
    UI_PATH = QTCREATORFILE

logging.basicConfig(level=logging.INFO)

DEFAULT_STATUS_BAR_TIMEOUT = 3000  # ms
DATETIME_FORMAT = 'yyyyMMdd_hhmmss'
ORGANIZATION = "Boston Dynamics"
APPLICATION_NAME = "BDDF Download"


def simple_ping(hostname):
    """Sends a short ping request to the desired IPv4 hostname.

    Args:
        hostname (string) IPv4 address of the robot

    Returns:
        exit_code (int) return status from the ping request
    """
    current_os = platform.system().lower()
    if current_os == "windows":
        parameter = "-n"
    else:
        parameter = "-c"
    exit_code = subprocess.call(['ping', parameter, '1', '-w', '2', hostname],
                                stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return exit_code


class BDDFDownloadGui(QtWidgets.QMainWindow):
    """Graphical user interface to download BDDF logs from the robot."""

    def __init__(self, *args, **kwargs):
        super(BDDFDownloadGui, self).__init__(*args, **kwargs)
        uic.loadUi(UI_PATH, self)

        self.setup_default_time(minutes_before=30)
        self.sdk = bosdyn.client.create_standard_sdk('bddf_download_gui.py')

        # Button clicking.
        self.btn_download.clicked.connect(self.download)
        self.btn_ping.clicked.connect(self.ping)
        self.btn_select_all.clicked.connect(self.select_all)
        self.btn_save_as.clicked.connect(self.save_as)
        self.btn_check_timesync.clicked.connect(self.check_timesync)
        self.btn_check_data_buffer.clicked.connect(self.check_data_buffer_size)
        self.pb_get_events_comments.clicked.connect(self.display_operator_comments)


        # If any input field is changed, regenerate the command.
        self.le_hostname.textChanged.connect(self.generate_download_command)
        self.le_hostname.textChanged.connect(self.clear_required_fields)
        self.le_username.textChanged.connect(self.generate_download_command)
        self.le_password.textChanged.connect(self.generate_download_command)
        self.le_output_filepath.textChanged.connect(self.generate_download_command)
        self.le_output_filename.textChanged.connect(self.generate_download_command)
        self.le_val.textChanged.connect(self.generate_download_command)
        self.le_channel.textChanged.connect(self.generate_download_command)
        self.dte_1.dateTimeChanged.connect(self.generate_download_command)
        self.dte_2.dateTimeChanged.connect(self.generate_download_command)
        self.cb_use_date_time.stateChanged.connect(self.generate_download_command)
        self.cb_append_timespan.stateChanged.connect(self.generate_download_command)
        self.cb_use_date_time.stateChanged.connect(self.use_date_time_switch)

        # Use QSettings for application state.
        self.settings = QtCore.QSettings(ORGANIZATION, APPLICATION_NAME)
        self.settings_dict = {
            'hostname': self.le_hostname,
            'username': self.le_username,
            'password': self.le_password,
            'output_filepath': self.le_output_filepath,
            'channel': self.le_channel,
        }
        self.readSettings()

        self.generate_download_command()

    def line_edit_settings(self, write=False):
        """Function helper for reading and writing to QLineEdits of previous user session.

        Args:
            write (bool) read or write to line edit.
        """
        for key, value in self.settings_dict.items():
            if write:
                self.settings.setValue(key, value.text())
            else:
                value.setText(self.settings.value(key))

    def readSettings(self):
        """Read from QSettings."""
        self.line_edit_settings(write=False)

    def writeSettings(self):
        """Write to QSettings."""
        self.line_edit_settings(write=True)

    def closeEvent(self, event):
        """Call writeSettings on window close event."""
        self.writeSettings()

    def clear_required_fields(self):
        """Clear the timesync and data buffer fields if hostname changes."""
        self.le_check_data_buffer.clear()
        self.le_timesync.clear()

    def get_authenticated_robot_client(self):
        """Returns authenticated robot sdk object."""
        robot = self.sdk.create_robot(self.le_hostname.text())
        # Check if communication is possible.
        if not self.ping():
            return False
        try:
            robot.authenticate(self.le_username.text(), self.le_password.text())
            return robot
        except Exception as e:
            error_message = f'Failed to connect/authenticate: {e}'
            self.statusBar().showMessage(error_message, DEFAULT_STATUS_BAR_TIMEOUT)
            return False

    def check_data_buffer_size(self):
        """Displays the current robot data buffer size."""
        robot = self.get_authenticated_robot_client()
        if robot is not False:
            client = robot.ensure_client(DataServiceClient.default_service_name)
            status = client.get_data_buffer_status()
            data_buffer_size = status.data_buffer_status.data_buffer_total_bytes
            str_data_buffer_size = f'{data_buffer_size/1e9:0.3f} GB'
            self.le_check_data_buffer.setText(str_data_buffer_size)

    def check_timesync(self):
        """Check and report time difference between robot and client."""
        clock_skew = self.get_clock_skew()
        if clock_skew:
            self.le_timesync.setText(duration_str(clock_skew))

    def get_clock_skew(self):
        """Returns the client to robot clock_skew."""
        robot = self.get_authenticated_robot_client()
        if robot is not False:
            endpoint = TimeSyncEndpoint(robot.ensure_client(TimeSyncClient.default_service_name))
            if not endpoint.establish_timesync(break_on_success=False):
                logging.debug("Failed to achieve time sync.")
                return False
            return endpoint.clock_skew

    def generate_download_command(self):
        """Generate equivalent bddf_download.py command."""
        hostname, username, password, timespan, output, channel = self.return_all_arguments()

        command = (f'python3 bddf_download.py {hostname} '
                   f'--username {username} '
                   f'--password PASSWORD '
                   f'-T {timespan} '
                   f'-o {output}')

        # If channel is defined, append as an argument.
        if channel:
            command = f'{command} -c {channel}'

        self.te_command.setText(command)

    def return_all_arguments(self):
        """Return all arguments required for simple bddf_download.py."""
        hostname = self.le_hostname.text()
        username = self.le_username.text()
        password = self.le_password.text()
        timespan = self.get_timespan_string()
        output = self.get_output()
        channel = self.le_channel.text()

        return hostname, username, password, timespan, output, channel

    def save_as(self):
        """Use file browser to specify output filepath and filename."""
        output = self.get_output()
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save As", output,
                                                             "BDDF Files (*.bddf)")
        output_filepath, output_filename = os.path.split(file_name)
        self.le_output_filepath.setText(output_filepath)
        self.le_output_filename.setText(output_filename)

    def select_all(self):
        """Quickly select all text used for bddf_download.py command."""
        self.te_command.selectAll()

    def get_output(self):
        """Get output filepath and filename for format for bddf_download.py."""
        output_filepath = self.le_output_filepath.text()
        output_filename = self.le_output_filename.text()

        file_extension = '.bddf'
        output_filename = os.path.splitext(output_filename)[0]
        if self.cb_append_timespan.isChecked():
            output_filename = f'{output_filename}_{self.get_timespan_string()}{file_extension}'
        else:
            output_filename = f'{output_filename}{file_extension}'

        output_filename = output_filename.replace(" ", "_")
        total_filepath = os.path.join(output_filepath, output_filename)

        return total_filepath

    def setup_default_time(self, minutes_before):
        """Default time options on program startup.

        Args:
            minutes_before (int) number of minutes to use for the datetime timespan.
        """
        current_time = QtCore.QDateTime.currentDateTime()
        # Set second {val} as current time.
        self.dte_2.setDateTime(current_time)
        python_current_time = current_time.toPyDateTime()
        # Set first {val} sometime before.
        val_1_time = python_current_time - datetime.timedelta(minutes=minutes_before)
        self.dte_1.setDateTime(val_1_time)

    def get_timespan_string(self):
        """Get timespan string from date time edits and format for bddf_download.py."""
        raise_filesize_limit_flag = False
        timespan = None

        if self.cb_use_date_time.isChecked():
            datetime_1 = self.dte_1.dateTime()
            datetime_2 = self.dte_2.dateTime()

            if datetime_2.toPyDateTime() - datetime_1.toPyDateTime() > datetime.timedelta(hours=1):
                raise_filesize_limit_flag = True
            else:
                raise_filesize_limit_flag = False

            timespan = datetime_1.toString(DATETIME_FORMAT) + '-' + datetime_2.toString(
                DATETIME_FORMAT)
        else:
            timespan = self.le_val.text()

        if raise_filesize_limit_flag is True:
            self.statusBar().showMessage(f'File size to large. Do not exceed 60 minutes.',
                                         DEFAULT_STATUS_BAR_TIMEOUT)
            self.statusBar().setStyleSheet("background-color : red")
        else:
            self.statusBar().setStyleSheet("")

        return timespan

    def download(self):
        """Perform the BDDF download and update with download percentage."""
        hostname, username, password, timespan, output, channel = self.return_all_arguments()
        if not hostname:
            self.statusBar().showMessage(f'Please specify a hostname.', DEFAULT_STATUS_BAR_TIMEOUT)
            return

        robot = self.get_authenticated_robot_client()
        if robot is False:
            return

        output = os.path.expanduser(output)
        if os.path.exists(output):
            self.statusBar().showMessage(f'Filepath already exists: {output}',
                                         DEFAULT_STATUS_BAR_TIMEOUT)
            return

        filepath = os.path.split(output)[0]
        if not os.path.exists(filepath):
            os.makedirs(filepath, exist_ok=True)

        self.statusBar().showMessage('Download started, please wait...', DEFAULT_STATUS_BAR_TIMEOUT)

        # If channel is defined, use as an argument.
        use_channel = None
        if channel:
            use_channel = channel.split()  # for multiple channels, split by space character

        url, headers, params = prepare_download(robot, timespan, channel=use_channel,
                                                message_type=None, service=None)

        self.pb.setValue(0)
        number_of_bytes_processed = 0
        for chunk, total_content_length, response_status_code in collect_and_write_file(
                url, headers, params, output):
            # Check for success status response.
            if response_status_code != 200:
                self.statusBar().showMessage(
                    f'Unable to get data. https response: {response_status_code}',
                    DEFAULT_STATUS_BAR_TIMEOUT)
                return False
            else:
                number_of_bytes_processed = number_of_bytes_processed + chunk
                total_size_of_request = total_content_length
                if total_size_of_request == 0:
                    bytes_processed_string = f'Data is chunked. Number of megabytes processed: {number_of_bytes_processed/1e6:.0f} [MB].'
                    self.label_filesize.setText(bytes_processed_string)
                else:
                    self.label_filesize.setText(
                        f'Download progress: {number_of_bytes_processed/1e6:.2f} [MB] of {total_size_of_request/1e6:.2f} [MB]'
                    )
                    percentage_compete = (number_of_bytes_processed / total_size_of_request) * 100
                    download_percentage_string = f"Download is {percentage_compete:.2f}% complete."
                    logging.debug(download_percentage_string)
                    self.pb.setValue(percentage_compete)
                # Hack to get the label_filesize to update quickly.
                QtCore.QCoreApplication.processEvents()

        self.statusBar().showMessage(f'Download complete: {output}')

    def ping(self):
        """Ping robot and update status bar."""
        hostname = self.le_hostname.text()
        status = simple_ping(hostname)
        if status == 0:
            self.statusBar().showMessage(f'Ping of {hostname} was successful.',
                                         DEFAULT_STATUS_BAR_TIMEOUT)
            return True
        else:
            self.statusBar().showMessage(f'Ping of {hostname} FAILED.', DEFAULT_STATUS_BAR_TIMEOUT)
            return False

    def use_date_time_switch(self, new_state):
        """Toggle timespan options.

        Args:
            new_state (int) New checked state return from QCheckBox.
        """
        if new_state == 2:
            self.dte_1.setEnabled(True)
            self.dte_2.setEnabled(True)
            self.le_val.setEnabled(False)
        else:
            self.dte_1.setEnabled(False)
            self.dte_2.setEnabled(False)
            self.le_val.setEnabled(True)

    def display_operator_comments(self):
        """Display operator comments in QListWidget."""
        robot = self.get_authenticated_robot_client()
        if robot is not False:
            data_service_client = robot.ensure_client(DataServiceClient.default_service_name)
            data_response = data_service_client.get_events_comments(
                EventsCommentsSpec(comments=True))
            self.lw_comments.clear()
            for comment in data_response.events_comments.operator_comments:
                string_to_display = f'{comment.timestamp.ToDatetime().strftime("%Y-%m-%d %H:%M:%S")} | {comment.message}'
                self.lw_comments.addItem(string_to_display)


def main():
    """Start GUI and handle interrupt."""
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtWidgets.QApplication(sys.argv)
    window = BDDFDownloadGui()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
