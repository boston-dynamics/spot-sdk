# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Poll mission state for questions, answering them with predetermined codes."""
import argparse
import logging
import re
import time

import bosdyn.client
import bosdyn.client.util
from bosdyn.mission.client import MissionClient

LOGGER = logging.getLogger(__name__)

# Code to set on success.
SUCCESS_CODE = 0
# Code to set on failure.
FAILURE_CODE = -1

def monitor_loop(client, callback, interval_seconds=1):
    """Call out to 'callback' when a question is seen in mission state."""
    while True:
        time.sleep(interval_seconds)
        state = client.get_state()
        LOGGER.debug('Got state: \n%s', str(state))

        if not state.questions:
            continue

        # Just grab the first question available. There may be more!
        question = state.questions[0]

        available_options = set(option.answer_code for option in question.options)
        if available_options != set([SUCCESS_CODE, FAILURE_CODE]):
            LOGGER.warning('Available options did not match expected options!')

        answer_code = callback(question.text)
        LOGGER.info('Replying to question %i', question.id)
        try:
            client.answer_question(question.id, answer_code)
        except (bosdyn.client.RpcError, bosdyn.client.ResponseError):
            LOGGER.exception('Error while answering %i', question.id)


def do_something(sleep_seconds, question_text, regex):
    """Do something based on the question text.

    Returns an integer response code, to be used in an AnswerQuestion RPC.
    """
    try:
        # Put your code here. It can take as long as you want -- the robot will pause until you
        # respond.
        if regex.match(question_text):
            LOGGER.info('Question text "%s" matches regex "%s"', question_text, regex.pattern)
        else:
            LOGGER.info('Question text "%s" does NOT match regex "%s"', question_text,
                        regex.pattern)
        time.sleep(sleep_seconds)
        answer_code = SUCCESS_CODE
    except Exception: # pylint: disable=broad-except
        LOGGER.exception("Failed to do the thing, aborting the mission")
        answer_code = FAILURE_CODE
    return answer_code


def main():
    """Run the program."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument('--wait', default=0.1, type=float,
                        help='Number of seconds to wait before answering.')
    parser.add_argument(
        '--match-text', default='.*',
        help='Only match questions whose text matches this regex. Matches all text by default.')
    options = parser.parse_args()
    bosdyn.client.util.setup_logging(options.verbose)

    # Create an SDK that knows about the MissionClient type.
    sdk = bosdyn.client.create_standard_sdk('mission-Q&A-code-example', [MissionClient])
    sdk.load_app_token(options.app_token)
    robot = sdk.create_robot(options.hostname)
    robot.authenticate(options.username, options.password)
    client = robot.ensure_client(MissionClient.default_service_name)
    LOGGER.info('Beginning mission monitoring...')
    regex = re.compile(options.match_text)
    try:
        monitor_loop(client, lambda text: do_something(options.wait, text, regex))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
