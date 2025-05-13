# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import base64
import socket
import ssl
import time
from threading import Thread

SERVER_RECONNECT_DELAY = 60  # seconds of delay before retry after server error
SOCKET_TIMEOUT = 10  # socket timeout in seconds
SOCKET_MAX_RECV_TIMEOUTS = 12  # number of timeouts before reconnecting

DEFAULT_NTRIP_SERVER = ""
DEFAULT_NTRIP_PORT = 2101
DEFAULT_NTRIP_TLS_PORT = 2102


class NtripClientParams:
    """
    Class for storing parameters for connecting an NTRIP client to an NTRIP server.
    """

    def __init__(self, server=DEFAULT_NTRIP_SERVER, port=DEFAULT_NTRIP_PORT, user="", password="",
                 mountpoint="", tls=False):
        """
        Constructor.
        """
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.mountpoint = mountpoint
        self.tls = tls


class NtripClient:
    """
    Client used to connect to an NTRIP server to download GPS corrections. These corrections are
    then forwarded on to the GPS device using the given stream.
    """

    def __init__(self, device, params: NtripClientParams, logger):
        """
        Constructor.
        """
        self.device = device
        self.host = params.server
        self.port = params.port
        self.user = params.user
        self.password = params.password
        self.mountpoint = params.mountpoint
        self.tls = params.tls

        self.thread = None
        self.streaming = False
        self.sock = None

        self.logger = logger

    def make_request(self):
        """
        Make a connection request to an NTRIP server.
        """
        auth_str = base64.b64encode(f"{self.user}:{self.password}".encode()).decode()
        request = (f"GET /{self.mountpoint} HTTP/1.1\r\n"
                   f"Host: {self.host}:{self.port}\r\n"
                   "User-Agent: NTRIP Python Client\r\n"
                   "Accept: */*\r\n"
                   f"Authorization: Basic {auth_str}\r\n"
                   "Connection: close\r\n"
                   "\r\n")
        return request.encode()

    def start_stream(self):
        """
        Start streaming data from an NTRIP server to a GPS receiver.
        """
        if self.streaming:
            self.stop_stream()
        self.thread = Thread(target=self.stream_data_worker, daemon=True)
        self.thread.start()

    def stop_stream(self):
        """
        Stop streaming NTRIP data.
        """
        self.streaming = False
        if self.thread:
            self.thread.join()
        self.thread = None

    def is_streaming(self):
        """
        Determine if we are streaming NTRIP data.
        """
        return self.streaming

    def send_gga(self, gga):
        """
        Given a GPGGA message, send it to the NTRIP server. This helps the NTRIP server send
        corrections that are applicable to the area in which the receiver is operating.
        """
        if self.sock:
            try:
                self.sock.send(gga.encode())
            except OSError:
                self.logger.warning("Error sending GGA")
                return False
            return True
        return False

    def create_icy_session(self):
        """
        NTRIP Rev1 uses Shoutcast (ICY). Create an ICY session to stream RTCM data.
        """
        try:
            # Create a socket connection to the host and port.
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.tls:
                self.logger.info("Using secure connection")
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=self.host)
            sock.settimeout(SOCKET_TIMEOUT)
            self.logger.info("Connecting to NTRIP Server.")
            sock.connect((self.host, self.port))
            self.logger.info("Connected to NTRIP Server.")

            # Send the request.
            self.logger.info("Sending NTRIP Request.")
            sock.send(self.make_request())
            # Read a chunk of data, expecting to get the status line and headers.
            response = sock.recv(1024)

            response_lines = response.split(b"\r\n")
            if len(response_lines) < 2:
                self.logger.error("Invalid response from server: %s", response)
                return False
            status = response_lines[0].decode().split(" ")
            self.logger.info(response_lines[0].decode())
            if status[1] != "200":
                self.logger.error("HTTP Error: %s, retrying in %d seconds",
                                  response_lines[0].decode(), SERVER_RECONNECT_DELAY)
                sock.close()
                time.sleep(SERVER_RECONNECT_DELAY)
                return False
            self.logger.info("NTRIP Request Response received.")
            for line in range(1, len(response_lines)):
                if response_lines[line] == b"":
                    # Empty line, end of headers.
                    # The rest of the response contains data.
                    response = b"\r\n".join(response_lines[line + 1:])
                    break
                self.logger.info(response_lines[line])

            if response:
                self.handle_ntrip_data(response)

            # Make the socket available for sending GGA.
            self.sock = sock
            return True
        except (socket.herror, socket.gaierror):
            self.logger.warning("Error connecting to server %s:%d", self.host, self.port)
            return False
        except (TimeoutError, socket.timeout):
            self.logger.warning("Connection timeout")
            return False

    def stream_data(self):
        """
        Stream NTRIP data from a connected server and send it to a GPS receiver.
        """

        # NTRIP Rev1 uses Shoutcast (ICY), which looks a lot like HTTP but isn't quite the same.
        # Create an ICY session here to talk to an NTRIP Rev1 caster.
        ok = self.create_icy_session()
        if not ok:
            self.logger.error("Failed to create NTRIP Rev1 ICY session.")
            return

        timeouts = 0
        has_data = False
        while self.streaming and timeouts < SOCKET_MAX_RECV_TIMEOUTS:
            try:
                response = self.sock.recv(2048)
                if response:
                    timeouts = 0
                    self.handle_ntrip_data(response)
                    if not has_data:
                        self.logger.info("Received NTRIP data.")
                        has_data = True
                else:
                    self.logger.warning("Connection closed by server")
                    break
            except (socket.herror, socket.gaierror):
                self.logger.warning("Error connecting to server %s:%d", self.host, self.port)
            except (TimeoutError, socket.timeout):
                self.logger.exception("Socket timeout.")
                timeouts += 1

        self.logger.info("NTRIP stream closed. Closing socket.")
        # Close the socket.
        try:
            self.sock.close()
        except OSError:
            pass
        self.sock = None

        self.logger.info("NTRIP client finished.")

    def stream_data_worker(self):
        """
        NTRIP client worker thread function.
        """
        self.streaming = True
        while self.streaming:
            self.stream_data()

    def handle_ntrip_data(self, data):
        """
        Callback for handling NTRIP data.
        """
        # Send to receiver as is.
        self.device.write(data)

    def handle_nmea_gga(self, sentence):
        """
        Process an NMEA-GGA sentence passed in as a string.
        """
        fields = sentence.split(",")
        if len(fields) < 7:
            return
        quality = int(fields[6] or 0)
        if quality not in (0, 6):  # No fix or estimated.
            if not self.send_gga(sentence + "\r\n"):
                # Something went wrong, restart the stream.
                self.start_stream()
