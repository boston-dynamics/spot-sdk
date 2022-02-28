<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Boston Dynamics Choreography Tablet Screen

Dances authored and executed using Choreographer can also be played through the Tablet using the Choreography drive mode.

## Choreography Safety

When playing any choreography sequence on a robot, always keep in mind basic safety procedures. Make sure there is plenty of space around your Spot, keep all Spots at least two meters apart from each other, and be sure that neither you nor anyone else approach the dancing Spot. Never approach your Spot unless its motors have been powered off.

## Using the Choreography Drive Mode

<img src="images/tablet_choreographer_1.png" width="520"/> 

1) **Application selection** - The Choreography Drive Mode can be entered from the upper left dropdown menu where it will appear with Drive and Autowalk.
2) **Exiting and Entering Dance Mode** - For Tablets without hardware joysticks exiting and entering dance mode will allow you to toggle between playing choreography sequences and using the other robot modes (walk, stand, sit, etc.) For tablets with hardware joysticks selected choreography sequences will always appear on screen.
3) **Select and View Known Moves** - A list of the choreography sequences that the robot can perform are viewable by pressing the **Select Moves** tab at the top of the screen. Opening this menu will also allow you to add dance sequences to the Choreography screen as buttons which are used to play the sequences on the robot.

    *The tablet interface refers to entire sequences as "Moves."*

<img src="images/tablet_choreographer_2.png" width="520"/> 

4) **Adding Moves to the Screen** - You can choose to place any sequence to the left or right side of the tablet screen, where it will be added to a list of buttons which each trigger the playback of the selected choreography sequence. Swipe horizontally left and right across the dropdown menu to scroll through the known moves.

<img src="images/tablet_choreographer_3.png" width="520"/> 

5) **Play the Choreography Sequence** - Once a sequence appears on screen as a white button you can press that button to play the choreography sequence. The name on the button indicates the choreography sequence that will play.
6) **Removing Buttons from the list** - You can remove a button from on screen by pressing the black ‘minus’ symbol next to it. This will not remove it from the list of available sequences in the **Select Moves** dropdown menu.
7) **Cancel Move** - A choreography sequence that is playing can be stopped by pressing the red **CANCEL** button in the center of the screen. If a move is canceled while it is playing the robot will stop the move and come to stand. A sequence can also be aborted by entering any other mode (e.g. Sit, Stand, Walk, Self Right).

## Using the Tablet to Play your own Choreography Sequences
Spot comes with a small library of sequences, some intended for performance, and some gestures that could be used to communicate intent through body language. These sequences are always available in the Select Moves dropdown, but the Tablet can also play custom sequences uploaded by users. The easiest way to author choreography sequences and upload them to the robot is through the Choreographer application. 

*Only users with a Spot choreography license can upload original sequences.*

**Uploading Choreography Sequences with Choreographer** 

1) Start by opening your completed choreography sequence in Choreographer and connecting your robot to Choreographer. Refer to the “Choreographer User Guide” and “Connecting Robots to Choreographer” if you have trouble with this step.

2) Make sure you have given your choreography sequence a name that will allow you to easily identify it later, and then play the sequence on the robot using the Choreographer application. Playing the sequence on the robot uploads it to Spot’s memory.

3) After repeating steps 1 and 2 for all the choreography sequences you want to play through the tablet, sit the robot and disconnect it from Choreographer. Now when you connect to Spot through the Tablet all your original choreography sequences will appear with the other moves in the **Select Moves** dropdown menu.

**Limitations on Original Sequences** 
Custom sequences uploaded by users to Spot are not saved permanently; they will only remain available until the robot is powered off. After turning the robot back on, you must follow follow all the steps in, “Uploading Choreography Sequences with Choreographer” again to reupload your sequences. 

