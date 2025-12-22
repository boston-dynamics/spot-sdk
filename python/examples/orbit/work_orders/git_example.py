# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

# Boston Dynamics, Inc. Confidential Information.
# Copyright 2025. All Rights Reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging
import os
from typing import Dict

import requests
from flask import Flask, jsonify, request

SECRET = os.getenv("INTEGRATION_SECRET")
if not SECRET:
    raise RuntimeError("Missing INTEGRATION_SECRET environment variable")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise RuntimeError("Missing GITHUB_TOKEN environment variable")

GITHUB_REPO = os.getenv("GITHUB_REPO")
if not GITHUB_REPO:
    raise RuntimeError("Missing GITHUB_REPO environment variable")

GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/issues"

# Configure and set up logging
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
log_format = "Work Order App: %(levelname)s - %(message)s\n"
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter(log_format))
LOGGER.addHandler(ch)

# Initialize Flask app
app = Flask(__name__)


@app.before_request
def verify_auth_header():
    secret_value = request.headers.get("x-integration-secret")
    if not secret_value or secret_value != SECRET:
        return jsonify({"Error": "Invalid secret"}), 401


def get_github_auth_headers() -> Dict:
    return {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}


# This endpoint allows Orbit to create a new work order. Any fields in the request data
# should be extracted and translated to the appropriate GitHub issue fields. In this case we are using the same field names in Orbit
# as GitHub (title, body), but this could be adapted as needed.
@app.post("/work_order")
def create_work_order():
    LOGGER.info("Handling create request")
    data = request.get_json()
    title = data.get("title", "No Title Provided")
    body = data.get("body", "")
    payload = {"title": title, "body": body}

    # If the request includes an image attachment and our external system supports it, we can include it here.
    # image_base64 = data.get("image_base64", None)
    # if image_base64:
    #     # Either include the image in the body
    #     payload["image"] = image_base64
    #     # Or handle image upload separately and include a link in the body
    #     image_url = upload_image_somewhere(image_base64)
    #     payload["body"] += f"\n\n![Image]({image_url})"
    try:
        # Send the create issue request to GitHub API.
        response = requests.post(GITHUB_API_URL, json=payload, headers=get_github_auth_headers())
        if not response.ok:
            message = f"Failed to create GitHub issue. Error Code: {response.status_code}. Error: {response.text}"
            LOGGER.error(message)
            return jsonify({"Error": message}), response.status_code
        issue = response.json()
        # Return a simplified response. We could also return the full response and change the Orbit configuration to match.
        return jsonify({
            "id": issue.get("number"),  # Use the issue number as the work order ID
            "title": issue.get("title"),
            "url": issue.get("html_url")
        }), 200
    except Exception as e:
        LOGGER.error(f"Failed to create GitHub issue {e}")
        return jsonify({"Error": str(e)}), 500


# This endpoint allows Orbit to query the status of a work order by its ID (GitHub issue number).
@app.get("/work_order/<id>/status")
def get_work_order_status(id):
    LOGGER.info(f"Handling status request for GitHub issue {id}")
    try:
        int(id)
    except ValueError as e:
        LOGGER.error(f"Failed to parse ID {id} as an int {e}")
        return jsonify({"Error": "Value of id must be an integer"}), 400
    try:
        url = f"{GITHUB_API_URL}/{id}"
        # Retrieve the GitHub issue corresponding to the work order ID (GitHub issue number).
        response = requests.get(url, headers=get_github_auth_headers())
        if not response.ok:
            message = f"Failed to get GitHub issue. Error Code: {response.status_code}. Error: {response.text}"
            LOGGER.error(message)
            return jsonify({"Error": message}), response.status_code
        issue = response.json()
        # We will return the full issue data for simplicity. Similar to creation, we could adapt this to return a simplified response.
        return jsonify(issue), 200
    except Exception as e:
        return jsonify({"Error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=21605, debug=False)
