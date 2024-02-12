<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Choreography in Autowalk

As of Spot Release 4.0.0, choreography sequences can be added as Execute Choreography Actions in autowalk missions.

*Only users with a Spot choreography license have access to choreography actions within the tablet autowalk application.*

## Choreography safety

When playing any mission containing choreography actions on a robot, always keep in mind basic safety procedures. Make sure there is plenty of space around your Spot where a choreography action will be played. Make sure that neither you nor anyone else will approach the dancing Spot during the mission. Remember that robots running choreography actions are not capable of reacting to their surroundings, and will hit obstacles if they are in the path of the dancing robot. Missions with Choreography Actions should not run unsupervised.

## Adding Choreography Actions to Autowalk Missions

For more details about autowalk and missions, see the [Autowalk Service documentation](../autonomy/autowalk_service.md) and the [Mission Service documentation](../autonomy/missions_service.md).

To begin, start a recording for a new autowalk mission using the tablet. Navigate Spot to where you want your first choreography action to start and click on the action menu:

<img src="autowalk_images/recording_action_menu.png" width="520"/>

In the action menu, select the **Actions** tab, and then select **Choreography**.

<img src="autowalk_images/choreography_in_list.png" width="520"/>

Use the Choreography Action screen to select a choreography sequence to add to the autowalk as an autowalk action:

<img src="autowalk_images/choreography_options_screen.png" width="520"/>

1. Select the name of the sequence to add.

    note: Sequences must be loaded to the robot before they will be available during the autowalk recording process. To see details on playing choreography sequences through the tablet, see the [Choreography in Tablet](../choreography/choreography_in_tablet.md) documentation.

2. The **Preview** button will play the selected choreography sequence, without adding it to the mission as an action.

3. The **Stop** button will stop the robot if it is currently performing a previewed choreography sequence.

4. The **Create** button will add the selected choreography sequence to the autowalk as a Choreography Action.

5. To configure the Choreography Action before adding it to the autowalk, press the **Configure** button.

## Using Autowalk to Store and Transfer Choreography Sequences and Animations

In addition to playing choreography sequences, a recorded walk file will store and save all the choreography sequences and animated moves it needs to perform the added choreography actions, so there is no need to ensure that a robot has the required sequences for the autowalk once the mission has been recorded.

Users can save previously unknown sequences contained in the autowalk to a different Spot through the Choreography Settings screen once that mission has been successfully loaded to the robot.
