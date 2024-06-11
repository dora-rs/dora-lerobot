import argparse
import os
import time
from pathlib import Path

# import h5py
import numpy as np
import pyarrow as pa
from dora import Node
from reachy2_sdk import ReachySDK

freq = 30

ROBOT_IP = "192.168.1.42"
# ROBOT_IP = "localhost"

reachy = ReachySDK(ROBOT_IP)

SIMULATION = False

reachy.turn_on()

time.sleep(1)
action = [
    2.70750225e-02,
    3.76733482e-01,
    -1.79577127e-01,
    -1.60979617e00,
    -1.09046809e-02,
    6.97152093e-02,
    1.92173451e-01,
    1.71317685e00,
    5.88761508e-01,
    -7.00486451e-03,
    -1.59729898e-01,
    -2.03063869e00,
    -1.12172333e-04,
    -3.93478051e-02,
    1.20750383e-01,
    1.96845388e00,
    0.00000000e00,
    0.00000000e00,
    0.00000000e00,
    4.07035090e-02,
    4.09805328e-01,
    -1.20783195e-01,
]


reachy.l_arm.goto_joints(action[0:7], duration=2.0, degrees=False)
reachy.r_arm.goto_joints(action[8:15], duration=2.0, degrees=False)

time.sleep(5)

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
            # reachy.l_arm.gripper.set_opening(
            #     min(100, max(0, action[7] / 2.26 * 100))
            # )  # replay true action value
            reachy.l_arm.gripper.set_opening(
                0 if action[7] < 2.0 else 100
            )  # trick to force the gripper to close fully

            reachy.r_arm.shoulder.pitch.goal_position = np.rad2deg(action[8])
            reachy.r_arm.shoulder.roll.goal_position = np.rad2deg(action[9])
            reachy.r_arm.elbow.yaw.goal_position = np.rad2deg(action[10])
            reachy.r_arm.elbow.pitch.goal_position = np.rad2deg(action[11])
            reachy.r_arm.wrist.roll.goal_position = np.rad2deg(action[12])
            reachy.r_arm.wrist.pitch.goal_position = np.rad2deg(action[13])
            reachy.r_arm.wrist.yaw.goal_position = np.rad2deg(action[14])
            # reachy.r_arm.gripper.set_opening(
            #     min(100, max(0, action[15] / 2.26 * 100))
            # )  # replay true action value
            reachy.r_arm.gripper.set_opening(
                0 if action[15] < 2.0 else 100
            )  # trick to force the gripper to close fully
            reachy.mobile_base.set_speed(action[16], action[17], np.rad2deg(action[18]))
            reachy.head.neck.roll.goal_position = np.rad2deg(action[19])
            reachy.head.neck.pitch.goal_position = np.rad2deg(action[20])
            reachy.head.neck.yaw.goal_position = np.rad2deg(action[21])
        case "tick":
            if not SIMULATION:
                mobile_base_pos = reachy.mobile_base.odometry
            else:
                mobile_base_pos = {"vx": 0, "vy": 0, "vtheta": 0}
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
                "mobile_base_vx": np.deg2rad(mobile_base_pos["vx"]),
                "mobile_base_vy": np.deg2rad(mobile_base_pos["vy"]),
                "mobile_base_vtheta": np.deg2rad(mobile_base_pos["vtheta"]),
                "head_roll": np.deg2rad(reachy.head.neck.roll.present_position),
                "head_pitch": np.deg2rad(reachy.head.neck.pitch.present_position),
                "head_yaw": np.deg2rad(reachy.head.neck.yaw.present_position),
            }

            node.send_output("agent_pos", pa.array(qpos.values()))
