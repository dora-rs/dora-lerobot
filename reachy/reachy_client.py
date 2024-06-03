import argparse
import os
import time
from pathlib import Path

import h5py
from reachy2_sdk import ReachySDK
from pollen_vision.camera_wrappers.depthai import SDKWrapper
from pollen_vision.camera_wrappers.depthai.utils import get_config_file_path
import pyarrow as pa
from dora import Node
import numpy as np

freq = 30

cam_name = "cam_trunk"

cam = SDKWrapper(get_config_file_path("CONFIG_SR"), fps=freq)
# ret, image = cap.read()
reachy = ReachySDK("localhost")
reachy.turn_on()
time.sleep(1)

# start = time.time()
node = Node()

for event in node:
    id = event["id"]
    match id:
        case "action":
            action = event["value"].to_numpy()
            reachy.l_arm.shoulder.pitch.goal_position = np.rad2deg(action[0])
            reachy.l_arm.shoulder.roll.goal_position = np.rad2deg(action[1])
            reachy.l_arm.elbow.yaw.goal_position = np.rad2deg(action[2])
            reachy.l_arm.elbow.pitch.goal_position = np.rad2deg(action[3])
            reachy.l_arm.wrist.roll.goal_position = np.rad2deg(action[4])
            reachy.l_arm.wrist.pitch.goal_position = np.rad2deg(action[5])
            reachy.l_arm.wrist.yaw.goal_position = np.rad2deg(action[6])
            reachy.l_arm.gripper.set_opening(action[7])

            reachy.r_arm.shoulder.pitch.goal_position = np.deg2rad(action[8])
            reachy.r_arm.shoulder.roll.goal_position = np.deg2rad(action[9])
            reachy.r_arm.elbow.yaw.goal_position = np.deg2rad(action[10])
            reachy.r_arm.elbow.pitch.goal_position = np.deg2rad(action[11])
            reachy.r_arm.wrist.roll.goal_position = np.deg2rad(action[12])
            reachy.r_arm.wrist.pitch.goal_position = np.deg2rad(action[13])
            reachy.r_arm.wrist.yaw.goal_position = np.deg2rad(action[14])
            reachy.r_arm.gripper.set_opening(action[15])
        case "tick":
            cam_data, _, _ = cam.get_data()

            left_rgb = cam_data["left"]

            qpos = {
                "l_arm_shoulder_pitch": np.deg2rad(
                    reachy.l_arm.shoulder.pitch.present_position
                ),
                "l_arm_shoulder_roll": np.deg2rad(
                    reachy.l_arm.shoulder.roll.present_position
                ),
                "l_arm_elbow_yaw": np.deg2rad(reachy.l_arm.elbow.yaw.present_position),
                "l_arm_elbow_pitch": np.deg2rad(
                    reachy.l_arm.elbow.pitch.present_position
                ),
                "l_arm_wrist_roll": np.deg2rad(
                    reachy.l_arm.wrist.roll.present_position
                ),
                "l_arm_wrist_pitch": np.deg2rad(
                    reachy.l_arm.wrist.pitch.present_position
                ),
                "l_arm_wrist_yaw": np.deg2rad(reachy.l_arm.wrist.yaw.present_position),
                "l_gripper": reachy.l_arm.gripper._present_position,
                "r_arm_shoulder_pitch": np.deg2rad(
                    reachy.r_arm.shoulder.pitch.present_position
                ),
                "r_arm_shoulder_roll": np.deg2rad(
                    reachy.r_arm.shoulder.roll.present_position
                ),
                "r_arm_elbow_yaw": np.deg2rad(reachy.r_arm.elbow.yaw.present_position),
                "r_arm_elbow_pitch": np.deg2rad(
                    reachy.r_arm.elbow.pitch.present_position
                ),
                "r_arm_wrist_roll": np.deg2rad(
                    reachy.r_arm.wrist.roll.present_position
                ),
                "r_arm_wrist_pitch": np.deg2rad(
                    reachy.r_arm.wrist.pitch.present_position
                ),
                "r_arm_wrist_yaw": np.deg2rad(reachy.r_arm.wrist.yaw.present_position),
                "r_gripper": reachy.r_arm.gripper._present_position,
            }

            node.send("agent_pos", pa.array(qpos.values()))
            node.send("cam_trunk", left_rgb)
