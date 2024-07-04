# Dora pipeline Robots

AlexK Low Cost Robot is a low-cost robotic arm that can be teleoperated using a similar arm. This repository contains
the Dora pipeline to manipulate the arms, the camera, and record/replay episodes with LeRobot.

## Recording

This section explains how to record episodes for LeRobot using the AlexK Low Cost Robot.

Recording is the process of teleoperating the robot and saving the episodes to a dataset. The dataset is used to train
the robot to perform tasks autonomously.

To record episodes with Dora, you have to configure the Dataflow `record_mono_teleop_real.yml` file to integrate the
arms and the camera. The graph file is located in the `graphs` folder.

Make sure to:

- Adjust the serial ports of `lcr_leader` and `lcr_follower` in the `record_mono_teleop_real.yml` file.
- Adjust the camera ID in the `record_mono_teleop_real.yml` file.
- Adjust camera and video WIDTH and HEIGHT in the `record_mono_teleop_real.yml` file, if needed.
- Adjust OFFSETS and DRIVE_MODES environment variables in the `record_mono_teleop_real.yml` file for both arms.

You can now start the Dora pipeline to record episodes for LeRobot:

```bash
cd dora-dora_lerobot

# If you are using a custom environment, you will have to activate it before running the command
source [your_custom_env_bin]/activate

# If you followed the installation instructions, you can run the following command
source venv/bin/activate # On Linux
source venv/Scripts/activate # On Windows bash
venv\Scripts\activate.bat # On Windows cmd
venv\Scripts\activate.ps1 # On Windows PowerShell

dora up
dora start ./robots/alexk_lcr/graphs/record_mono_teleop_real.yml
```

Then, you can tele operate the follower with the leader. A window will pop up showing the camera feed, and some text.

1. Press space to start/stop recording
2. Press return if you want to tell the recording that you failed the current episode, or the previous episode if you
   have not started the current one
3. Close the window to stop the recording
4. Write down the location of the logs (e.g `018fc3a8-3b76-70f5-84a2-22b84df24739`), this is where the
   dataset (and logs) are stored.

You can now use our script to convert the logs to a dataset:

```bash
cd dora-dora_lerobot

TODO: Add the script to convert the logs to a valid dataset

```

## The dora graph

[![](https://mermaid.ink/img/pako:eNqVVD1vwyAQ_SuIOYnb1UOHqmundgsRusA5QcXGAtwPVf3vPXBiOY6bpB6s4_Heu-N85psrp5GXnB2eyroPtQcf2eujaBizykuLoNEfV6aJ6FtnIeIRqpwlWU9xLTbqXSqo0UMmoHdbF6VH5bxOiHYeDst1MVoIsRFN6LY7D-2eSSnznpRsnYJNko53o6EUh3ci5Siz-hRFBoraWGtCcX-3FmKIi8zDhurJr2mZbLlk0ag3BoG1nbWydcFE4xraeJg25UxJlgPvQrsSdfClREf8PNmMSZ9_atGj1w3-edjxB57YJfHOwUhELh_eRJSn8KzX5TpMDTvMwrOpOgGSsOeSMgfUnir2KWfHbzobQ-p5yS1nBjUcczzT8wPSmkD_XZIdQrLX-HmbugJjUeeJyZG86vF3t9w2oH-HVPoqg2FFLNm1s6VcGN6xUYh9k04M-IJT9hqMpuvmO9kJHvdYo-AlhRor6GwUXDQ_RIUuupevRvEy-g4X3Ltut-dlBTbQqms1ZXgyQJdBPaCoTXT-ub_Q8r328wvwVb3i?type=png)](https://mermaid.live/edit#pako:eNqVVD1vwyAQ_SuIOYnb1UOHqmundgsRusA5QcXGAtwPVf3vPXBiOY6bpB6s4_Heu-N85psrp5GXnB2eyroPtQcf2eujaBizykuLoNEfV6aJ6FtnIeIRqpwlWU9xLTbqXSqo0UMmoHdbF6VH5bxOiHYeDst1MVoIsRFN6LY7D-2eSSnznpRsnYJNko53o6EUh3ci5Siz-hRFBoraWGtCcX-3FmKIi8zDhurJr2mZbLlk0ag3BoG1nbWydcFE4xraeJg25UxJlgPvQrsSdfClREf8PNmMSZ9_atGj1w3-edjxB57YJfHOwUhELh_eRJSn8KzX5TpMDTvMwrOpOgGSsOeSMgfUnir2KWfHbzobQ-p5yS1nBjUcczzT8wPSmkD_XZIdQrLX-HmbugJjUeeJyZG86vF3t9w2oH-HVPoqg2FFLNm1s6VcGN6xUYh9k04M-IJT9hqMpuvmO9kJHvdYo-AlhRor6GwUXDQ_RIUuupevRvEy-g4X3Ltut-dlBTbQqms1ZXgyQJdBPaCoTXT-ub_Q8r328wvwVb3i)

## License

This library is licensed under the [Apache License 2.0](../../LICENSE).