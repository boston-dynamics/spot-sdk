# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Poll mission state for questions, answering them with predetermined codes."""
import argparse
import logging
import time

import six.moves

import bosdyn.client
import bosdyn.client.util
from bosdyn.mission.client import MissionClient

LOGGER = logging.getLogger(__name__)


def monitor_loop(client, interval_seconds=1):
    """Call out to 'callback' when a question is seen in mission state."""
    while True:
        time.sleep(interval_seconds)
        state = client.get_state()
        LOGGER.debug('Got state: \n%s', str(state))

        if not state.questions:
            continue

        # Just grab the first question available. There may be more!
        question = state.questions[0]
        answer_code = ask_user_for_answer(question)
        LOGGER.info('Replying to question %i', question.id)
        try:
            client.answer_question(question.id, answer_code)
        except (bosdyn.client.RpcError, bosdyn.client.ResponseError):
            LOGGER.exception('Error while answering %i', question.id)


def ask_user_for_answer(question_proto):
    """Ask the user for a response to the given Question message.

    Returns an integer response code, to be used in an AnswerQuestion RPC.
    """
    selection_number = 1
    # Build a list of tuples, each tuple is (Text associated with the option, answer_code)
    user_options = []
    for option in question_proto.options:
        user_options.append(('{}) {}'.format(selection_number, option.text), option.answer_code))
        selection_number += 1

    text = 'Question: "{}"\n\nChoose one:\n'.format(question_proto.text)
    text += ''.join(opt[0] + '\n' for opt in user_options)
    idx = int(six.moves.input(text)) - 1
    return user_options[idx][1]


def main():
    """Run the program."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args()
    bosdyn.client.util.setup_logging(options.verbose)

    # Create an SDK that knows about the MissionClient type.
    sdk = bosdyn.client.create_standard_sdk('mission-Q&A-code-example', [MissionClient])
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    client = robot.ensure_client(MissionClient.default_service_name)
    LOGGER.info('Beginning mission monitoring...')
    try:
        monitor_loop(client)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
