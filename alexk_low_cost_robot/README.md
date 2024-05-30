# recording a dataset with A. Koch robot arm

## Hardware setup:
Pipeline designed for a teleoperated 5 DoF + gripper arm such as the arm by [A. Koch (build with the extension)](https://github.com/AlexanderKoch-Koch/low_cost_robot) and with 2 cameras to record images.

## Install

Follow dora instructions to install dora.

Git clone this repo.

## Setup the dora graph

The dora graph is at `alexk_low_cost_robot/example/record_teleop.yml`

1. adjust the serial ports for the master and puppet arms as env variables in : `MASTER_PATH`, `PUPPET_PATH`, `CAMERA_ID`

On ubuntu find the path to the arms with the dynamixel wizard for instance and the path to the cameras with `v4l2-ctl --list-devices`.

2. Adjust the `source` to the locations of your python env for each node

## Steps to setup and record

Start dora with ` dora up`

Then do:
1. Start the graph `dora start ./example/record_teleop.yml`
2. Press space to move to the next episode and save the previous one
3. Press esc when finished with all
4. Pressing backspace will end the current episode, save it and wait until space is pressed to start a new episode
5. After having pressed esc, type `dora stop` to stop the recording.
6. Write down the location of the logs (a long hash like `018fc3a8-3b76-70f5-84a2-22b84df24739`), this is where the dataset (and logs) are stored.
