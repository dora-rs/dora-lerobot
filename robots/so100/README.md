# Dora pipeline for teleoperated low-cost arm and episode recording for LeRobot

SO-ARM100 is a low-cost robotic arm that can be teleoperated using a similar arm. This repository contains
the Dora pipeline to record episodes for LeRobot.

## Assembling

Check the [ASSEMBLING.md](ASSEMBLING.md) file for instructions on how to assemble the robot from scratch.

## Installations

Check the [INSTALLATIONS.md](INSTALLATION.md) file for instructions on how to install the required software and
environment
to run the robot.

## Calibration

Calibration is a critical step to ensure your SO-ARM100 functions correctly. We provide a simplified calibration tool to guide you through the process:

```bash
cd dora-lerobot/

# Activate your environment
source venv/bin/activate # On Linux
source venv/Scripts/activate # On Windows bash
venv\Scripts\activate.bat # On Windows cmd
venv\Scripts\activate.ps1 # On Windows PowerShell

# Run the calibration script
python ./robots/so100/calibrate_so_arm100.py --port <YOUR_PORT> --left
# Or use --right if your arm is positioned on the right side
```

The calibration script will:
1. Connect to your SO-ARM100 arm
2. Guide you through positioning the arm in reference positions
3. Calculate the necessary calibration parameters
4. Save the configuration to a file
5. Let you verify the calibration with real-time feedback

For more detailed calibration information, check the [CONFIGURING.md](CONFIGURING.md) file.

## Configuring

Check the [CONFIGURING.md](CONFIGURING.md) file for instructions on how to configure the robot to record episodes for
LeRobot and teleoperate the robot.

## Recording

It's probably better to check the [examples](#examples) below before trying to record episodes. It will give you a
better
understanding of how Dora works.

Check the [RECORDING.md](RECORDING.md) file for instructions on how to record episodes for LeRobot.

## Examples

There are also some other example applications in the `graphs` folder. Have fun!

Here is a list of the available examples:

There are also some other example applications in the `graphs` folder. Have fun!

Here is a list of the available examples:

- `mono_teleop_real_with_alexk_lcr.yml`: A simple real teleoperation pipeline that allows you to control a follower arm
  using a leader
  arm. It
  does not record the episodes, so you don't need to have a camera.

You must configure the arms, retrieve the device port, and modify the file `mono_teleop_real_with_alexk_lcr.yml` to set
the correct
environment variables. (e.g. `PORT` and `CONFIG`, `LEADER_CONTROL` and `FOLLOWER_CONTROL`)

```bash
cd dora-lerobot/

# If you are using a custom environment, you will have to activate it before running the command
source [your_custom_env_bin]/activate

# If you followed the installation instructions, you can run the following command
source venv/bin/activate # On Linux
source venv/Scripts/activate # On Windows bash
venv\Scripts\activate.bat # On Windows cmd
venv\Scripts\activate.ps1 # On Windows PowerShell

dora build ./robots/so100/graphs/mono_teleop_real_with_alexk_lcr.yml # Only the first time, it will install all the requirements if needed

dora up
dora start ./robots/so100/graphs/mono_teleop_real_with_alexk_lcr.yml
```

## License

This library is licensed under the [Apache License 2.0](../../LICENSE).
