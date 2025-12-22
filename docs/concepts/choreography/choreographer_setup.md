<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Install Choreographer

The Choreographer application allows you to easily author sequences by combining and parameterizing a variety of pre-defined moves and custom animations as well as execute on the robot with music synchronization.

The application can be downloaded from the [Boston Dynamics Support Center](https://support.bostondynamics.com/s/downloads) (login required). Most Choreography API commands require a special license to use.

## System requirements

Choreographer supports 64-bit Microsoft Windows 11 and 64-bit Ubuntu 22.04 Linux. No other system dependencies are required to run the Choreographer application.

_When using the Choreography SDK independently of the Choreographer application, both Python 3 and the `bosdyn-api` and `bosdyn-choreography-client` wheels must be installed._

## Installing and running Choreographer

The Choreographer application is an executable which can be run directly on a laptop or desktop computer. Download the `choreographer.exe` (Windows) or `choreographer` (Linux) executable from the [Boston Dynamics Support Center](https://support.bostondynamics.com/s/downloads).

### Granting Permissions

**For Windows**: When running Choreographer for the first time, Windows will likely display a security warning stating that the publisher is unknown. This happens because Choreographer is not digitally signed, and it does not indicate an issue with the program. You can select "more info" -> "run anyway".

**For Linux**: When running Choreographer, it will likely be necessary to grant executable permissions for the `choreographer` application file before it can be executed. You can grant permission to run the application by right-clicking the file, selecting "properties" -> "Permissions", and enabling the "Allow executing file as program" option.

You can also grant permissions on Linux through the command line by running the following command:

```
sudo chmod +x {FILEPATH_TO_CHOREOGRAPHER}
```

### Running Choreographer

To run Choreographer, double-click on the executable to open it or run it from command line.

- On windows:
  ```
  {FILEPATH_TO_CHOREOGRAPHER}
  ```
- On Linux:

  ```
  ./{FILEPATH_TO_CHOREOGRAPHER}
  ```

## Installing Optional Choreographer Dependencies

Some Choreographer features such as loading and viewing music files and [timecode](timecode_reference.md) support require the installation of additional audio/video libraries.

- Full music loading capability and displaying music waveforms requires **FFmpeg** (supports audio decoding) or **Gstreamer** (Windows-only alternative to FFmpeg).
- Timecode features require **PortAudio** (audio device I/O support).

### FFmpeg (recommended)

#### Linux Installation

Most Linux distributions include FFmpeg in their default repositories, and can be installed with the below commands:

```
sudo apt update
sudo apt install ffmpeg
```

#### Windows Installation

1. Download a prebuilt Windows FFmpeg package (e.g., “full” build from a trusted provider such as Gyan or BtbN).
2. Extract the contents in an easily accessible location, such as:
   ```
   C:\ffmpeg\
   ```
3. Add FFmpeg's bin folder to your **PATH**:
   - Open "System Properties" -> "Advanced" -> "Environment Variables"
   - Under "System variables" (or "User variables"), select "Path" and click "Edit"
   - Click "New" and add:
     ```
     C:\ffmpeg\bin
     ```
4. Verify the installation by opening a new Command Prompt and running:
   ```
   ffmpeg -version
   ```

### Gstreamer (Alternative to FFmpeg)

#### Windows Installation

1. Download the MSVC 64-bit runtime and development installers.
2. Install both packages.
3. Add GStreamer's bin folder to your **PATH**:
   - Open "System Properties" -> "Advanced" -> "Environment Variables"
   - Under "System variables" (or "User variables"), select "Path" and click "Edit"
   - Click "New" and add (adjust path if you installed to a different location):
     ```
     C:\gstreamer\1.0\msvc_x86_64\bin
     ```
   - Click "OK" on all dialogs
4. Verify the installation by opening a new Command Prompt and running:

   ```
   gst-launch-1.0 --version
   ```

   _Note: If both FFmpeg and GStreamer are installed, Choreographer may default to FFmpeg._

### PortAudio

#### Linux Installation

The below command installs PortAudio along with its required library dependencies:

```
sudo apt-get install libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0
```

#### Windows Installation

PortAudio may already be present on your Windows machine. If it is not available and timecode features are disabled, follow the below steps to manually install PortAudio.

1. Download a prebuilt PortAudio DLL:
   - Check [PortAudio's download page](http://www.portaudio.com/download.html) for official releases
2. Place the DLL file (e.g., `portaudio_x64.dll` or `portaudio.dll`) in one of these locations:

   - In the same directory as the Choreographer executable, OR
   - In a directory added to your **PATH** environment variable (see FFmpeg instructions above for how to modify PATH)

3. Check that PortAudio is correctly installed by relaunching Choreographer and checking that timecode features can be enabled in the timecode settings section of the "Settings"->"Playback and Music" menu.

## Contacting Support

The Boston Dynamics Support Center can be accessed by navigating to [http://support.bostondynamics.com](http://support.bostondynamics.com) from a web browser on any device.

Authenticated Support Center users with login credentials can submit and monitor support cases within **My Cases** and access the **Downloads** page, where Choreographer is available.

You can also reach Boston Dynamics Technical Support for help activating your Support Center account or to request a password reset by emailing **support@bostondynamics.com**.

### Opening Support Cases

When opening choreography-related support cases, please include as much of the information as you can for the following categories. This will aid our team in giving you the best and speediest resolution. (If certain information is unknown, that's okay! Please reach out to us anyway and we'll work with you to fix the problem).

#### Choreographer Application Issue

- Description of the issue.
- Application version and commit id information (found under "Help"->"About").
- Operating system.
- Terminal or Command Prompt error messages (if available).
- Any files (sequence, animation, music, etc.) being used at time of failure (if available/relevant).
- Screenshots or screen recording of the issue (if available).

#### Spot Failure when Performing a Choreography Sequence

- Description of the issue.
- Choreography sequence (.chr or .csq file)\* that produced the failure on Spot.
  - _\*Please also include any custom animation files (.cha) used in the sequence_ (if any).
- Experiment log or other automatically generated logs from the time of the failure (if available).
- Video of Spot when the issue occurred (if available).
- If Spot was being controlled by Choreographer at the time of the failure, please include:
  - Application version and commit id information.
  - Operating system.
  - Terminal or Command Prompt error messages at time of failure (if available).
