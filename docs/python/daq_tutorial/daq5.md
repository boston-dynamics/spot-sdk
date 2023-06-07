<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

<script type="text/javascript" src="video_play_at_scroll.js"></script>
<link rel="stylesheet" type="text/css" href="tutorial.css">
<link href="prism.css" rel="stylesheet" />
<script src="prism.js"></script>

[<< Previous Page](daq4.md)
|
[Next Page >>](daq6.md)

---

# Part 5: Collecting Data

In this part of the tutorial, you will:

- Create an action on the tablet to capture data from the services we wrote.
- Record a mission using those actions around your environment.
- Play back the mission to autonomously capture data a the recorded locations.
- Download the data from the robot.
- Configure the robot to automatically upload its data to the cloud.

To collect data we will create an [Autowalk mission](https://support.bostondynamics.com/s/article/Getting-Started-with-Autowalk) with Spot.

## Creating Actions

For our data collection, we want to capture from _both_ sources. We will create a new action "web_cam_battery" that captures both. To do that, navigate to Settings -> Actions from the hamburger menu.

![Settings/Actions](img/settings_actions.jpg)

Then, click `Create New Action`, which brings up the menu shown below to choose a template.

![Action Template](img/action_choose_template.jpg)

Select the `Empty Inspection` template and click `CREATE`. The following window pops up, where you can update the action name to "web_cam_battery", select `Daq` option. Then, select `Data Acquisition Battery - Battery` as the Data Acquisition Plugin and add another Data Acquisition Plugin for `Data Acquisition - Basic Position Data`. Finally, click `+ Add Images` and then and select `Web Cam - Video0`:

![New action video selection](img/web_cam_action1.jpg)

## Testing the action

You may now drive the robot around and trigger the new action.
This will cause it to capture both the web cam image and the battery data. This data can be downloaded from the "Download Data" in the hamburger menu, where you will be able to see the images captured directly on the tablet.

## Mission Recording

Follow these steps to record a mission with the new captures:

1. First select `Autowalk` from the drop-down menu in the top-left corner of the app, and then select `Record`.
   ![AutoWalk Record](img/autowalk_record.jpg)

2. Enter mission name.
   ![AutoWalk Mission Name](img/autowalk_mission_name.jpg)

3. Stand the robot up and move it near a fiducial, if necessary. The app displays those two warnings till both are satisfied. The robot automatically detects fiducials in the robot cameras field of view.
   ![AutoWalk Find Fiducial](img/autowalk_find_fiducial.jpg)

4. Start recording.
   ![AutoWalk Start Recording](img/autowalk_start_recording.jpg)

5. Move robot to location where to capture data.

6. Then, click the Red Plus button, select `INSPECTIONS` and choose `web_cam_battery` action.
   ![Choose Action](img/autowalk_action_choose.jpg)

7. In the next screen, align the camera view with the arrows on the screen if necessary, and then click `Configure`.
   ![Action Confirm](img/action_configure.jpg)

8. In the next screen, click `Create` to create action.
   ![Action Create](img/autowalk_action_create.jpg)

9. Repeat steps 5-8 as desired.

10. When done recording the mission, click `Finish Recording` to save mission.
    ![AutoWalk Finish](img/autowalk_finish.jpg)

### Mission playback

Next, follow these steps to play back the mission recorded in the section above.

1. First select `Autowalk` from the drop-down menu in the top-left corner of the app, and then select `Playback`.
   ![AutoWalk Record](img/autowalk_record.jpg)

2. Select `DAQ_Tutorial_Mission` mission and click `Continue`, `Continue` and `Play Now` in the next screens and then press the green Play button in the final screen.

3. Move the robot near the fiducial at the beginning of the mission and click `Initialize`.

4. When the mission completes, download the captured data by clicking “Sit and View Data”.
   ![AutoWalk Sit View Data](img/autowalk_playback_view_data.jpg)

### Configure the robot to automatically upload its data to the cloud.

The [Post Docking Callbacks example](../../../python/examples/post_docking_callbacks/README.md) contains scripts to enable users to upload files saved during a data acquisition mission to various endpoints, with the target use case having the callback run when Spot docks at the end of an Autowalk mission. Please follow instructions in that example to set up a callback to upload the captured data to AWS when the robot docks.

## Head over to [Part 6: Processing Collected Data](daq6.md) >>

[<< Previous Page](daq4.md)
|
[Next Page >>](daq6.md)
