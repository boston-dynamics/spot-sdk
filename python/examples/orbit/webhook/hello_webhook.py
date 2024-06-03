# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
An example to show how to utilize webhooks using Orbit web API.
"""

import argparse
import logging
import secrets
import sys

from flask import Flask, jsonify, request
from requests import Response

from bosdyn.orbit.client import create_client
from bosdyn.orbit.exceptions import WebhookSignatureVerificationError
from bosdyn.orbit.utils import validate_webhook_payload

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
log_format = "webhook listener: %(levelname)s - %(message)s\n"
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter(log_format))
LOGGER.addHandler(ch)

app = Flask(__name__)

SECRET = secrets.token_hex(32)


@app.route('/', methods=['GET', 'POST'])
def webhook_listener() -> Response:
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

    data_type = data['type']
    if data_type in ('ACTION_COMPLETED', 'ACTION_COMPLETED_WITH_ALERT', 'TEST'):
        message = data['data']
        LOGGER.info('%s: %s', data_type, message)
    else:
        # If the 'type' field is not recognized, return a 400 Bad Request
        return jsonify({"error": "Unrecognized payload type"}), 400

    # Validate the webhook payload.
    signature = request.headers['Orbit-Signature']
    try:
        validate_webhook_payload(data, signature, SECRET)
    except WebhookSignatureVerificationError as e:
        LOGGER.exception(f'Webhook signature verification failed with the following error: {e}')
        return jsonify({"error": "Invalid webhook signature"}), 400
    except Exception as e:
        LOGGER.exception(f'Got at error while attempting to validate the webhook signature: {e}')
        return jsonify({"error": "Unexpected error while attempting to validate webhook signature"
                       }), 500

    return 'OK', 200


def hello_webhook(options: argparse.Namespace) -> bool:
    """A simple example to show how to use Orbit client to fetch list, create, update, and delete webhook instance on Orbit.
        This example also shows how to start the webhook listener given a webhook host IP and port number.

        Args:
            options(Namespace) : parsed args used for webhook configuration options
        Returns:
            Boolean to indicate whether the function succeeded or not
    """
    # Create Orbit client object
    client = create_client(options)
    # Example: Fetching the list of existing webhook instances
    get_webhook_response = client.get_webhook()
    webhook_urls = [item['url'] for item in get_webhook_response.json()]
    if not get_webhook_response.ok:
        LOGGER.error('get_webhook() failed: {}'.format(get_webhook_response.text))
        return False
    LOGGER.info("Current list of registered webhook instances: {}".format(
        get_webhook_response.json()))

    # Example: Creating new webhook instance, if not already existent
    webhook_url = "http://" + options.webhook_host + ":" + str(options.webhook_port)
    if webhook_url in webhook_urls:
        LOGGER.error('duplicate webhook url: {} already exists'.format(webhook_url))
        return False
    webhook_request = {
        "url": webhook_url,
        "enabled": options.enabled,
        "events": options.payload_types,
        "validateTlsCert": options.validate_TLS_cert,
        "secret": SECRET
    }
    post_webhook_response = client.post_webhook(json=webhook_request)
    if not post_webhook_response.ok:
        LOGGER.error('post_webhook() failed: {}'.format(post_webhook_response.text))
        return False
    webhook_uuid = post_webhook_response.json()['uuid']
    LOGGER.info("Webhook uuid {} is successfully created!".format(webhook_uuid))

    # Example: Updating the specific instance of webhook instance
    new_webhook_request = {
        "url": webhook_url,
        "enabled": False,  # simple example to disable this webhook
        "events": options.payload_types,
        "validateTlsCert": options.validate_TLS_cert,
        "secret": SECRET
    }
    update_webhook_response = client.post_webhook_by_id(webhook_uuid, json=new_webhook_request)
    if not update_webhook_response.ok:
        LOGGER.error('post_webhook_by_id() failed: {}'.format(update_webhook_response.text))
        return False
    LOGGER.info("Webhook uuid {} is successfully updated!".format(webhook_uuid))

    if options.delete_webhook_afterwards:
        # Example: Deleting the specific instance of webhook instance
        delete_webhook_response = client.delete_webhook(webhook_uuid)
        if not delete_webhook_response.ok:
            LOGGER.error('delete_webhook() failed: {}'.format(delete_webhook_response.text))
            return False
        LOGGER.info("Webhook uuid {} is successfully deleted!".format(webhook_uuid))
    else:
        app.run(host=options.webhook_host, port=options.webhook_port)

    return True


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', help='IP address associated with the Orbit instance',
                        required=True, type=str)
    parser.add_argument('--webhook-host', help='the http host address for the webhook listener',
                        required=False, default='0.0.0.0', type=str)
    parser.add_argument('--webhook-port', help='the port for hosting the webhook listener',
                        required=False, default=8080, type=int)
    parser.add_argument('--enabled', help='whether webhook is enabled / disabled', required=False,
                        default='True', type=bool)
    parser.add_argument('--payload-types', help='types of events to trigger webhook',
                        required=False, default=["ACTION_COMPLETED",
                                                 "ACTION_COMPLETED_WITH_ALERT"], type=list)
    parser.add_argument('--delete-webhook-afterwards',
                        help='if set to False (default), establishes and starts listening service',
                        required=False, default=False, type=bool)
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
    hello_webhook(options)


if __name__ == '__main__':
    if not main():
        sys.exit(1)
