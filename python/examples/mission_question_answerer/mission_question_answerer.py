# Copyright (c) 2019 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging
import re
import time

import bosdyn.client
import bosdyn.client.util
from bosdyn.mission.client import MissionClient
from bosdyn.mission import constants

logger = logging.getLogger(__name__)

def monitor_loop(client, callback=None, interval_seconds=1):
    """Call out to 'callback' when a question is seen in mission state."""
    answered_id = None
    mission_id = None
    while True:
        time.sleep(interval_seconds)
        state = client.get_state()
        logger.debug('Got state: \n%s', str(state))

        if not state.questions:
            continue

        # If there is more than one question, this question may not be for us.
        if len(state.questions) != 1:
            logger.warning('There are more questions (%i > 1) than I expected!', len(state.questions))
            continue

        question = state.questions[0]

        # If there are unexpected answer codes, this question may not be for us.
        available_answer_codes = set(option.answer_code for option in question.options)
        if available_answer_codes != constants.valid_answer_codes:
            logger.warning('There are different options than I expected!')
            continue

        answer_code = callback(question.text)
        logger.info('Replying to question %i', question.id)
        try:
            client.answer_question(question.id, answer_code)
        except (RpcError, ResponseError) as exc:
            logger.exception('Error while answering %i', question.id)



def do_something(sleep_seconds, question_text, regex):
    try:
        # Put your code here. It can take as long as you want -- the robot will pause until you
        # respond.
        if regex.match(question_text):
            logger.info('Question text "%s" matches regex "%s"', question_text, regex.pattern)
        else:
            logger.info('Question text "%s" does NOT match regex "%s"', question_text, regex.pattern)
        time.sleep(sleep_seconds)
        answer_code = constants.SUCCESS_ANSWER_CODE
    except Exception as e:
        logger.error("Failed to do the thing, aborting the mission. Error: %s", str(e))
        answer_code = constants.FAILURE_ANSWER_CODE
    return answer_code


def main():
    import argparse

    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument('--wait', default=0.1, type=float, help='Number of seconds to wait before answering.')
    parser.add_argument('--match-text', default='.*',
                        help='Only match questions whose text matches this regex. Matches all text by default.')
    options = parser.parse_args()
    bosdyn.client.util.setup_logging(options.verbose)

    # Create an SDK that knows about the MissionClient type.
    sdk = bosdyn.client.create_standard_sdk('mission-Q&A-code-example', [MissionClient])
    sdk.load_app_token(options.app_token)
    robot = sdk.create_robot(options.hostname)
    robot.authenticate(options.username, options.password)
    client = robot.ensure_client(MissionClient.default_service_name)
    logger.info('Beginning mission monitoring...')
    regex = re.compile(options.match_text)
    try:
        monitor_loop(client, lambda question_text: do_something(options.wait, question_text, regex))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()


