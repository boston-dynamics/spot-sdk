# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Poll mission state for questions, answering them with predetermined codes."""
import argparse
import logging
import time

import bosdyn.client
import bosdyn.client.util
from bosdyn.mission.client import MissionClient
from bosdyn.api import service_customization_pb2

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
        answer_code = None
        custom_params = None

        # Answer based on which question format is being asked
        if len(question.options) > 0:
            answer_code = ask_user_for_options_answer(question)
        elif question.HasField('custom_params'):
            custom_params = ask_user_for_custom_param_answer(question)
        else:
            LOGGER.warning('Encountered malformed question %i. Question must suppy either an options list or custom_params spec.', question.id)
            continue
        LOGGER.info('Replying to question %i', question.id)
        try:
            client.answer_question(question.id, answer_code, custom_params)
        except (bosdyn.client.RpcError, bosdyn.client.ResponseError):
            LOGGER.exception('Error while answering %i', question.id)


def ask_user_for_options_answer(question_proto):
    """Ask the user for an answer_code response to the given Question message with an 'options' list.

    Returns an integer response code, to be used in an AnswerQuestion RPC.
    """
    selection_number = 1
    # Build a list of tuples, each tuple is (Text associated with the option, answer_code)
    user_options = []
    for option in question_proto.options:
        user_options.append((f'{selection_number}) {option.text}', option.answer_code))
        selection_number += 1

    text = f'Question: "{question_proto.text}"\n\nChoose one:\n'
    text += ''.join(opt[0] + '\n' for opt in user_options)
    idx = int(input(text)) - 1
    return user_options[idx][1]

def ask_user_for_custom_param_answer(question_proto):
    """Ask the user for a custom_params DictParam response to the given Question message with a 'custom_params' spec.
    This example only parses BoolParam specs to support the accompanying example mission.

    Returns a DictParam, to be used in an AnswerQuestion RPC.
    """

    result = service_customization_pb2.DictParam()

    question_spec = question_proto.custom_params
    if len(question_proto.text) > 0:
        print(f'{question_proto.text}\n').
    for child_spec_key in question_spec.specs:
        child_spec = question_spec.specs[child_spec_key]
        spec_type = child_spec.spec.WhichOneof('spec')
        title = child_spec_key
        description = None
        # Add UserInterfaceInfo to the command line prompt
        if child_spec.HasField('ui_info'):
            if len(child_spec.ui_info.display_name) > 0:
                title = child_spec.ui_info.display_name
            if len(child_spec.ui_info.description) > 0:
                description = child_spec.ui_info.description
        text = f'{title}: "{description}"'
        custom_param_value = service_customization_pb2.CustomParam()
        match spec_type:
            case 'bool_spec':
                bool_result = query_bool_yes_no(text)
                custom_param_value.bool_value.value = bool_result
                result.values[child_spec_key].CopyFrom(custom_param_value)
            # To present an answer additional types of specs, add support here.
            case _:
                LOGGER.warning(f'Spec type {spec_type} is not supported by this example client.')
    return result

# A helper for prompting and processing yes/no input
def query_bool_yes_no(question):
    valid_answers = {
        "yes": True,
        "y": True,
        "no": False,
        "n": False
    }
    while True:
        choice = input(f'{question} [y/n]\n').lower()
        if choice in valid_answers:
            return valid_answers[choice]
        else:
            print("Please respond with '[y]es' or '[n]o'.\n")
            
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
