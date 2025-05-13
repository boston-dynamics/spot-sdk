# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Build a mission to showcase Prompt nodes and how to answer them.

To run the mission, use the "replay_mission" example.
To answer the question posed by the Prompt, run "mission_question_answerer.py".
"""

import argparse

# Import from this directory.
import mission_question_answerer

from bosdyn.api.mission import nodes_pb2, util_pb2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output_file', help='File to save the mission to.')
    options = parser.parse_args()

    # Build our prompt node with a very simple question to be answered.
    prompt = nodes_pb2.Prompt()
    # This is a hint to other systems that this Prompt is not meant to be displayed.
    prompt.for_autonomous_processing = True
    # This is the text that is typically displayed to the user. It will still be accessible in the
    # mission state if for_autonomous_processing is True.
    prompt.text = 'What should I do?'
    # The variable to write into in the blackboard. Only this prompt's descendant nodes will have
    # access to it. This will be used later in the Condition node.
    prompt.source = 'prompt_answer_code'
    # Add one of the valid responses.
    option = prompt.options_list.options.add()
    option.text = 'Succeed'
    option.answer_code = 0

    # Add one of the valid responses.
    option = prompt.options_list.options.add()
    option.text = 'Fail'
    option.answer_code = -1

    # Now, build the Condition node that checks for a SUCCESS response:
    #   0 == prompt_answer_code
    condition = nodes_pb2.Condition()
    condition.operation = nodes_pb2.Condition.COMPARE_EQ
    condition.lhs.const.int_value = 0
    # During execution, this node will read the value of "prompt_answer_code" out of the blackboard.
    condition.rhs.var.name = prompt.source
    # We expect it to be an integer.
    condition.rhs.var.type = util_pb2.VariableDeclaration.TYPE_INT

    # Pack the Condition implementation into a Node message.
    condition_node = nodes_pb2.Node(name='Check simple prompt is success')
    condition_node.impl.Pack(condition)

    # And set the node as the child of the Prompt, giving it access to it's "source" variable in
    # the blackboard.
    prompt.child.CopyFrom(condition_node)

    # Finally, pack the Prompt itself into a Node message.
    simple_prompt_node = nodes_pb2.Node(name='Ask a simple question')
    simple_prompt_node.impl.Pack(prompt)

    # Prompts can also be described using custom param specifications.
    # Build another prompt node with a custom param question to be answered.

    custom_param_prompt = nodes_pb2.Prompt()
    # This is a hint to other systems that this Prompt is not meant to be displayed.
    custom_param_prompt.for_autonomous_processing = True

    # This is the text that is typically displayed to the user. It will still be accessible in the
    # mission state if for_autonomous_processing is True.

    # This question is asked as a boolean to demonstrate a question with a different data format.
    # The question "What should I do?" can be replicated with a StringParam.Spec param specification.
    custom_param_prompt.text = 'Custom param question:'
    # The variable to write into in the blackboard. Only this prompt's descendant nodes will have
    # access to it. This will be used later in the Condition node.
    custom_param_prompt.source = 'custom_param_prompt_answer_code'

    CUSTOM_PARAM_QUESTION_KEY = 'question'

    # Add one of the valid responses.
    spec = custom_param_prompt.custom_params.specs[CUSTOM_PARAM_QUESTION_KEY]
    spec.spec.bool_spec.SetInParent()
    spec.ui_info.display_name = "Question"
    spec.ui_info.description = "Should I succeed?"

    # Now, build the Condition node that checks for a True response:
    #   True == custom_param_prompt_answer_code.values["question"].value
    condition = nodes_pb2.Condition()
    condition.operation = nodes_pb2.Condition.COMPARE_EQ
    condition.lhs.const.bool_value = True
    # During execution, this node will read the value of "prompt_answer_code" out of the blackboard.
    path_to_value = f'.values["{CUSTOM_PARAM_QUESTION_KEY}"].bool_value.value'
    condition.rhs.var.name = f"{custom_param_prompt.source}{path_to_value}"
    # We expect it to be an integer.
    condition.rhs.var.type = util_pb2.VariableDeclaration.TYPE_BOOL

    # Pack the Condition implementation into a Node message.
    condition_node = nodes_pb2.Node(name='Check custom param prompt is success')
    condition_node.impl.Pack(condition)

    # And set the node as the child of the Prompt, giving it access to it's "source" variable in
    # the blackboard.
    custom_param_prompt.child.CopyFrom(condition_node)

    # Finally, pack the Prompt itself into a Node message.
    custom_param_prompt_node = nodes_pb2.Node(name='Ask a custom param question')
    custom_param_prompt_node.impl.Pack(custom_param_prompt)

    # Create a Sequence with both prompts.
    sequence = nodes_pb2.Sequence()
    sequence.children.add().CopyFrom(simple_prompt_node)
    sequence.children.add().CopyFrom(custom_param_prompt_node)

    # Return a Node with the Sequence.
    sequence_node = nodes_pb2.Node()
    sequence_node.name = "Sequence of two different types of prompts"
    sequence_node.impl.Pack(sequence)

    # Write out the mission.
    with open(options.output_file, 'wb') as output:
        output.write(sequence_node.SerializeToString())


if __name__ == '__main__':
    main()
