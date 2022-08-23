# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Provides a very visible button to click to stop the robot."""
from __future__ import print_function

import argparse
import logging
import os
import signal
import sys
import threading
import traceback
from datetime import datetime

import grpc
from six.moves import queue

try:
    import PyQt5.QtCore as QtCore
    import PyQt5.QtWidgets as QtWidgets
    from PyQt5.QtGui import QIcon

# Enable backwards compatibility with Python2 via PyQt4
except ImportError:
    from PyQt4.QtGui import QIcon
    import PyQt4.QtGui as QtWidgets
    import PyQt4.QtCore as QtCore

import bosdyn.client.util
from bosdyn.api import estop_pb2 as estop_protos
from bosdyn.client.estop import EstopClient, EstopEndpoint, EstopKeepAlive

# Needed for dll call in Windows to set icon
if sys.platform == 'win32':
    import ctypes

STOP_BUTTON_STYLESHEET = ("background-color: red; font: bold 60px; border-width: 5px; "
                          "border-radius:20px; padding: 60px")
RELEASE_BUTTON_STYLESHEET = ("background-color: green; border-width: 5px; border-radius:20px; "
                             "padding: 10px")
ERROR_LABEL_STYLESHEET = 'font: bold 15px'


class EstopGui(QtWidgets.QMainWindow):
    """The GUI for the estop Button. Provides software estop."""

    disable_signal = QtCore.pyqtSignal()
    checkin_status_signal = QtCore.pyqtSignal('QString')
    got_status_signal = QtCore.pyqtSignal('QString')

    def __init__(self, hostname, client, timeout_sec, name=None, unique_id=None):
        QtWidgets.QMainWindow.__init__(self)

        self.logger = logging.getLogger("Estop GUI")

        self.disable_signal.connect(self.disable_buttons)
        self.checkin_status_signal.connect(self.set_status_label)
        self.got_status_signal.connect(self._launch_estop_status_dialog)
        self.status_extant = False
        self.quitting = False  # Used to tell threads to shutdown

        # Force server to set up a single endpoint system
        ep = EstopEndpoint(client, name, timeout_sec)
        ep.force_simple_setup()

        # Begin periodic check-in between keep-alive and robot
        self.estop_keep_alive = EstopKeepAlive(ep)

        # Configure UI.
        self.setCentralWidget(QtWidgets.QWidget())
        self.center_layout = QtWidgets.QVBoxLayout(self.centralWidget())
        self.center_layout.setAlignment(QtCore.Qt.AlignTop)
        self.center_layout.setSpacing(1)
        self.center_layout.setContentsMargins(1, 1, 1, 1)

        self.stop_button = QtWidgets.QPushButton(self)
        self.stop_button.setText('STOP')
        self.stop_button.clicked.connect(self.estop_keep_alive.stop)
        self.stop_button.setStyleSheet(STOP_BUTTON_STYLESHEET)
        self.stop_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                       QtWidgets.QSizePolicy.Expanding)
        self.center_layout.addWidget(self.stop_button)

        self.status_label = QtWidgets.QLabel('Starting...')
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setStyleSheet(ERROR_LABEL_STYLESHEET)
        self.center_layout.addWidget(self.status_label)

        self.release_button = QtWidgets.QPushButton(self)
        self.release_button.setText('Release')
        self.release_button.clicked.connect(self.estop_keep_alive.allow)
        self.release_button.setStyleSheet(RELEASE_BUTTON_STYLESHEET)
        self.center_layout.addWidget(self.release_button)

        self.setWindowTitle("E-Stop ({} {}sec)".format(hostname, timeout_sec))

        # Begin monitoring the keep-alive status
        thread = threading.Thread(target=self._check_keep_alive_status)
        thread.start()

    def do_status_rpc(self):
        """Make an rpc call to get the robot estop status."""
        try:
            status = self.estop_keep_alive.client.get_status()
            #pylint: disable=broad-except
        except Exception as exc:
            markup = 'Exception while getting status!'
            traceback.print_exc()
        else:
            markup = status_response_to_markup(status,
                                               my_id=self.estop_keep_alive.endpoint.unique_id)
        self.got_status_signal.emit(markup)

    def status(self):
        """Asynchronously request and print the endpoint status."""
        if self.status_extant:
            self.logger.info('Ignoring duplicate request for status')
            return
        self.status_extant = True
        self.logger.info('Getting estop system status')
        thread = threading.Thread(target=self.do_status_rpc)
        thread.start()

    def _check_keep_alive_status(self):
        """Monitor estop keep alive status and display status in GUI via Qt signals."""
        while not self.quitting:
            # Wait for queue to be populated. After timeout, check if GUI is still running.
            try:
                status, msg = self.estop_keep_alive.status_queue.get(timeout=1)  # blocking
            except queue.Empty:
                continue

            if status == EstopKeepAlive.KeepAliveStatus.OK:
                self.checkin_status_signal.emit('OK! {:%H:%M:%S}'.format(datetime.now()))
            elif status == EstopKeepAlive.KeepAliveStatus.ERROR:
                self.checkin_status_signal.emit(msg)
            elif status == EstopKeepAlive.KeepAliveStatus.DISABLED:
                self.disable_signal.emit()
            else:
                raise Exception("Unknown estop keep alive status seen: {}.".format(status))

    def disable_buttons(self):
        """Disable the estop buttons."""
        self.stop_button.setEnabled(False)
        self.release_button.setEnabled(False)
        self.stop_button.setText('(disabled)')
        self.release_button.setText('(disabled)')

    def set_status_label(self, status_msg):
        self.status_label.setText(status_msg)

    def _launch_estop_status_dialog(self, markup):
        self.status_extant = False
        d = QtWidgets.QMessageBox()
        d.setWindowTitle('SW Estop Status')
        d.setText(markup)
        d.exec_()

    def quit(self):
        """Shutdown estop keep-alive and all GUI threads."""
        self.estop_keep_alive.shutdown()
        self.quitting = True


def status_response_to_markup(status, my_id=None):
    """Convert an estop_protos.EstopSystemStatus to some HTML text.

    Args:
    status (string): The EstopSystemStatus to parse.
    my_id (string): Optionally specify an endpoint unique ID. If that ID is in the active estop system,
        additional text is inserted into the markup.
    Returns:
    A string with HTML tags that can be displayed in a UI element (e.g. a dialog box)
    """

    endpoints_data = [(e.endpoint.name,
                    '(me)' if my_id == e.endpoint.unique_id else '(not me)',
                    estop_protos.EstopStopLevel.Name(e.stop_level),
                    e.time_since_valid_response.seconds + e.time_since_valid_response.nanos / 1e9)\
                    for e in status.endpoints]
    msg = ''
    for data in endpoints_data:
        msg += '<b>{} {}</b>  {} (sent {:.2f} ago)<br>'.format(*data)
    net_level = estop_protos.EstopStopLevel.Name(status.stop_level)
    reason = status.stop_level_details
    markup = '<b>' + net_level + '</b>  (' + reason + ')<br><br>Endpoints:<br>' + msg

    return markup


def build_app(hostname, estop_client, timeout_sec):
    """Build the application window and configure the estop.
    Args:
      timeout_sec: Timeout of this estop endpoint (seconds)
    """
    qt_app = QtWidgets.QApplication(sys.argv)

    icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'stop-sign.png')
    icon_path = os.path.normpath(icon_path)
    icon = QIcon(icon_path)
    qt_app.setWindowIcon(icon)

    # Setting the taskbar icon in windows. See https://stackoverflow.com/a/1552105
    if sys.platform == 'win32':
        myappid = 'bostondynamics.estop_button.1'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    gui = EstopGui(hostname, estop_client, timeout_sec, name="EStop")
    return (qt_app, gui)


def run_app(qt_app, button_window):
    """Run the QT application."""
    button_window.show()

    retcode = qt_app.exec_()
    button_window.quit()
    return retcode


def build_and_run_app(hostname, estop_client, options):
    qt_app, button_window = build_app(hostname, estop_client, options.timeout)
    if qt_app is None or button_window is None:
        exit(1)

    # Set some Qt flags for our GUI behavior.
    if options.on_top:
        button_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    if options.start_minimized:
        button_window.setWindowState(QtCore.Qt.WindowMinimized)

    def sigint_handler(sig, frame):
        """Cleanly shut down the application on signal."""
        #pylint: disable=unused-argument
        button_window.quit()
        button_window.logger.info('Estop gui received signal for clean shutdown. Exiting.')
        exit(0)

    # Look for a signal for a clean shut-down.
    signal.signal(signal.SIGINT, sigint_handler)
    # Set up a timer to let the python interpreter run once every 100ms. This lets us catch signals.
    # From https://stackoverflow.com/a/4939113.
    timer = QtCore.QTimer()
    timer.start(100)
    # Temporarily break out of the QT event loop, so we can look at signals.
    timer.timeout.connect(lambda: None)

    return run_app(qt_app, button_window)


def main(argv):
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('-t', '--timeout', default=5, type=float, help='Timeout in seconds')
    parser.add_argument('--no-on-top', help='Allow window to be hidden.', dest='on_top',
                        action='store_false', default=True)
    parser.add_argument('--start-minimized', help='Start the window minimized.',
                        dest='start_minimized', action='store_true', default=False)
    options = parser.parse_args(argv)
    bosdyn.client.util.setup_logging(options.verbose)

    # Create robot object
    sdk = bosdyn.client.create_standard_sdk('estop_gui')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)

    # Create estop client for the robot
    estop_client = robot.ensure_client(EstopClient.default_service_name)

    exit(build_and_run_app(options.hostname, estop_client, options))


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
