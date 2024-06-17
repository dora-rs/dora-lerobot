# Dora pipeline for teleoperated low-cost arm and episode recording for LeRobot

AlexK Low Cost Robot is a low-cost robotic arm that can be teleoperated using a similar arm. This repository contains
the Dora pipeline to record episodes for LeRobot.

## Assembling

**Please read the instructions carefully before buying or printing the parts.**

You will need to get the parts for a Follower (= Puppet) arm and a Leader (= Master):

- [AlexK Puppet Low Cost Robot](https://github.com/AlexanderKoch-Koch/low_cost_robot/?tab=readme-ov-file#follower-arm)
- [AlexK Master Low Cost Robot](https://github.com/AlexanderKoch-Koch/low_cost_robot/?tab=readme-ov-file#follower-arm)

You **must** assemble the arm **with the extension** to be able to do some of the tasks.

You then need to print the puppet arm and the master arm. The STL files are:

- [AlexK Puppet Low Cost Robot](https://github.com/AlexanderKoch-Koch/low_cost_robot/tree/main/hardware/follower/stl)
- [AlexK Master Low Cost Robot](https://github.com/AlexanderKoch-Koch/low_cost_robot/tree/main/hardware/leader/stl)

Some parts **must** be replaced by the ones in this repository:

- [Dora-LeRobot Base Master Low Cost Robot](stl/MASTER_Base.stl)

If you struggle buying XL330 Frame or XL330 Idler Wheel, here are STL files that can be printed instead:

- [XL330 Frame](stl/XL330_Frame.stl)
- [XL330 Idler Wheel](stl/XL330_Idler_Wheel.stl)

Please then follow the [Youtube Tutorial by Alexander Koch](https://youtu.be/RckrXOEoWrk?si=ZXDnnlF6BQd_o7v8) to
assemble the arm correctly.
Note that the tutorial is for the arm without the extension, so you will have to adapt the assembly.

Then you can place the two cameras on your desk, following this [image]()

## License

This library is licensed under the [Apache License 2.0](../../LICENSE).