# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
An example to show how to utilize webhooks, host a listener on orbit and integrate this data with another system.
"""

import argparse
import base64
import logging
import os
import sys

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from requests import Response

from bosdyn.orbit.client import Client
from bosdyn.orbit.exceptions import WebhookSignatureVerificationError
from bosdyn.orbit.utils import validate_webhook_payload

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
log_format = "webhook: %(levelname)s - %(message)s\n"
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter(log_format))
LOGGER.addHandler(ch)

env_file = '../app/extension/.env'  # for docker

# Load environment variables from .env file
load_dotenv(env_file)
# Constants
SECRET = os.getenv("SECRET")
API_TOKEN = os.getenv("API_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL")

# Global variables
app = Flask(__name__)


class WebhookManager:

    def __init__(self, client, webhook_host, webhook_port, hostname):
        """
        Initialization method that sets up our webhook integrator object.
        
        Args:
            webhook_host: IP that the webhook listener will be hosted at 
            webhook_port: Port that the webhook listener will be hosted at
            client: Instantiated Orbit Client
            hostname: IP of the Orbit instance this integration will be connecting to
        """
        self.webhook_host = webhook_host
        self.webhook_port = webhook_port
        self.client = client
        self.hostname = hostname

    def run_listener(self):
        """
        Start our webhook listener / server
        """
        LOGGER.info("Running Server...")
        app.run(host=self.webhook_host, port=self.webhook_port, debug=True)

    @app.route('/', methods=['GET', 'POST'])
    def webhook_listener(self) -> Response:
        """Listens to incoming webhook requests from Orbit and processes them depending on the payload type.
            
            Returns:
                A tuple containing a response message and an HTTP status code.
        """
        # Get the JSON data from the incoming webhook
        data = request.json

        # If the request does not contain valid JSON data, return a 400 Bad Request
        if data is None:
            return jsonify({"error": "Invalid JSON data"}), 400
        # If the 'type' field is missing in the JSON data, return a 400 Bad Request
        if 'type' not in data:
            return jsonify({"error": "Missing 'type' field in JSON data"}), 400

        # Check if the incoming data contains a message specific to payload types
        if data['type'] == "ACTION_COMPLETED" or data['type'] == "ACTION_COMPLETED_WITH_ALERT":
            LOGGER.info("ACTION_COMPLETED:")
            for capture in data['data']['dataCaptures']:
                key_results = capture['keyResults']

                # Form our image URL request
                https = 'https://'
                image_path = capture['dataUrl']
                image_url = https + self.orbit_hostname + image_path

                # Grab image - method returns type: urllib3.response.HTTPResponse
                image = client.get_image(image_url)

                # Send image and check for errors
                if image.status == 200:
                    LOGGER.info("Image Response was 200... Retrieving info.")
                    # Encode HTTP response - you could alternatively just include the imageURL for later reference
                    encoded_image = base64.b64encode(image.data).decode()
                    capture['inspection_image'] = encoded_image
                    LOGGER.info("Image Embedded.")
                else:
                    LOGGER.info("Image response was not 200.")
                if key_results != None:
                    LOGGER.info("~~~~~~ Key Results ~~~~~~")
                    LOGGER.info(key_results)
            self.send_to_backend_service(data)

        elif data['type'] == "ACTION_COMPLETED_WITH_ALERT":
            # Do something different if it alerted instead
            message = data['data']
            LOGGER.info("ACTION_COMPETED_WITH_ALERT: ", message)

        elif data['type'] == "TEST":
            message = data['data']
            LOGGER.info("TEST: ")
            LOGGER.info(message)

        else:
            # If the 'type' field is not recognized, return a 400 Bad Request
            return jsonify({"error": "Unrecognized payload type"}), 400

        # Validate the webhook payload.

        # First get the Orbit signature for one part of the handshake
        try:
            signature = request.headers['Orbit-Signature']
        except Exception as e:
            LOGGER.exception(f'Not from an Orbit instance: {e}')
            return 'OK', 200

        LOGGER.info(f"Signature: {signature} \n Secret:{SECRET}")

        # Validate with the other half of the handshake we have preset from Orbit when making our Webhook
        try:
            validate_webhook_payload(data, signature, SECRET)
        except WebhookSignatureVerificationError as e:
            LOGGER.exception(f'Webhook signature verification failed with the following error')
            return jsonify({"error": "Invalid webhook signature"}), 400
        except Exception as e:
            LOGGER.exception(f'Got at error while attempting to validate the webhook signature')
            return jsonify(
                {"error": "Unexpected error while attempting to validate webhook signature"}), 500

        return 'OK', 200

    def send_to_backend_service(self, inspection_data):
        """Takes in the build JSON inspection data payload and forwards on using a REST API call.
            
            Args:
            inspection_data(JSON) : build JSON with data to be forwarded to the backend system
            
        """
        # Basic Authentication Credentials
        username = 'your_username'
        password = 'your_password'

        # Set 'Content-Type'
        headers = {'Content-Type': 'application/json'}

        LOGGER.info(f'Sending inspection data {inspection_data}')

        # Making a POST request to the webhook with basic authentication
        response = requests.post(BACKEND_URL, json=inspection_data, headers=headers)

        # Check for HTTP codes other than 200 (HTTP_OK)
        if response.status_code == 200:
            print('Success!')
            LOGGER.info(f'Successfull sent with status code {response.status_code}')
        else:
            print('Failed to call webhook with status code:', response.status_code)
            LOGGER.info(f'Failed to call webhook with status code:{response.status_code}')
            print('Response:', response.text)

    def create_webhook(self, options) -> bool:
        """A simple example to show how to use Orbit client to fetch list, create, update, and delete webhook instance on Orbit.
            This example also shows how to start the webhook listener given a webhook host IP and port number.
            
            Args:
                options(Namespace) : parsed args used for webhook configuration options
            Returns:
                Boolean to indicate whether the function succeeded or not
        """

        # Example: Fetching the list of existing webhook instances
        get_webhook_response = self.client.get_webhook()
        webhook_urls = [item['url'] for item in get_webhook_response.json()]
        if not get_webhook_response.ok:
            LOGGER.error('get_webhook() failed: {}'.format(get_webhook_response.text))
            return False
        LOGGER.info("Current list of registered webhook instances: {}".format(
            get_webhook_response.json()))

        # Example: Creating new webhook instance, if not already existent
        webhook_url = "http://" + self.webhook_host + ":" + str(self.webhook_port)
        webhook_request = {
            "url": webhook_url,
            "enabled": options.enabled,
            "validateTlsCert": options.validate_TLS_cert,
            "events": options.payload_types,
            "secret": SECRET
        }
        if webhook_url in webhook_urls:
            LOGGER.error('duplicate webhook url: {} already exists'.format(webhook_url))
        else:
            post_webhook_response = client.post_webhook(json=webhook_request)
            if not post_webhook_response.ok:
                LOGGER.error('post_webhook() failed: {}'.format(post_webhook_response.text))
            else:
                webhook_uuid = post_webhook_response.json()['uuid']
                return webhook_uuid, webhook_request


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', help='IP address associated with the Orbit instance',
                        required=True, type=str)
    parser.add_argument('--webhook-host', help='the http host address for the webhook listener',
                        required=False, default='0.0.0.0', type=str)
    parser.add_argument('--webhook-port', help='the port for hosting the webhook listener',
                        required=False, default='8080', type=str)
    parser.add_argument('--payload-types', help='types of events to trigger webhook',
                        required=False, default=["ACTION_COMPLETED",
                                                 "ACTION_COMPLETED_WITH_ALERT"], type=list)
    parser.add_argument('--enabled', help='whether webhook is enabled / disabled', required=False,
                        default='True', type=bool)
    parser.add_argument('--validate-TLS-cert', required=False, default='True', type=bool)
    parser.add_argument(
        '--verify',
        help=
        'verify(path to a CA bundle or Boolean): controls whether we verify the server’s TLS certificate',
        default=True,
    )
    parser.add_argument(
        '--cert', help=
        "(a .pem file or a tuple with ('cert', 'key') pair): a local cert to use as client side certificate ",
        nargs='+', default=None)
    options = parser.parse_args()

    global client
    # Determine the value for the argument "verify"
    if options.verify in ["True", "False"]:
        verify = options.verify == "True"
    else:
        print(
            "The provided value for the argument verify [%s] is not either 'True' or 'False'. Assuming verify is set to 'path/to/CA bundle'"
            .format(options.verify))
        verify = options.verify

    # A client object represents a single instance.
    client = Client(hostname=options.hostname, verify=verify, cert=options.cert)
    client.authenticate_with_api_token(API_TOKEN)

    webhook_manager = WebhookManager(client, webhook_host=options.webhook_host,
                                     webhook_port=int(options.webhook_port),
                                     hostname=options.hostname)
    webhook_manager.create_webhook(options)
    webhook_manager.run_listener()


if __name__ == '__main__':
    if not main():
        sys.exit(1)
