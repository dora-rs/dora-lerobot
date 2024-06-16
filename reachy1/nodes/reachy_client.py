import time

# import h5py
import numpy as np
import pyarrow as pa
from dora import Node
from reachy_sdk import ReachySDK

freq = 30

ROBOT_IP = "10.42.0.24"
# ROBOT_IP = "localhost"

reachy = ReachySDK(ROBOT_IP)
reachy.turn_off_smoothly("r_arm")
time.sleep(2)
reachy.turn_on("r_arm")
reachy.turn_on("head")

SIMULATION = False

time.sleep(5)

node = Node()
for event in node:
    id = event["id"]
    match id:
        case "action":
            action = event["value"].to_numpy()

            reachy.joints.r_shoulder_pitch.goal_position = np.rad2deg(action[0])
            reachy.joints.r_shoulder_roll.goal_position = np.rad2deg(action[1])
            reachy.joints.r_arm_yaw.goal_position = np.rad2deg(action[2])
            reachy.joints.r_elbow_pitch.goal_position = np.rad2deg(action[3])
            reachy.joints.r_forearm_yaw.goal_position = np.rad2deg(action[4])
            reachy.joints.r_wrist_pitch.goal_position = np.rad2deg(action[5])
            reachy.joints.r_wrist_roll.goal_position = np.rad2deg(action[6])
            reachy.joints.r_gripper.goal_position = action[7]
            # reachy.joints.neck_roll.goal_position = np.rad2deg(action[8])
            # reachy.joints.neck_pitch.goal_position = np.rad2deg(action[9])
            # reachy.joints.neck_yaw.goal_position = np.rad2deg(action[10])

        case "tick":
            # if not SIMULATION:
            # mobile_base_pos = reachy.mobile_base.odometry
            # else:
            # mobile_base_pos = {"vx": 0, "vy": 0, "vtheta": 0}
            qpos = {
                "r_shoulder_pitch": np.deg2rad(
                    reachy.joints.r_shoulder_pitch.present_position
                ),
                "r_shoulder_roll": np.deg2rad(
                    reachy.joints.r_shoulder_roll.present_position
                ),
                "r_arm_yaw": np.deg2rad(reachy.joints.r_arm_yaw.present_position),
                "r_elbow_pitch": np.deg2rad(
                    reachy.joints.r_elbow_pitch.present_position
                ),
                "r_forearm_yaw": np.deg2rad(
                    reachy.joints.r_forearm_yaw.present_position
                ),
                "r_wrist_pitch": np.deg2rad(
                    reachy.joints.r_wrist_pitch.present_position
                ),
                "r_wrist_roll": np.deg2rad(reachy.joints.r_wrist_roll.present_position),
                "r_gripper": reachy.joints.r_gripper.present_position,
                # "mobile_base_vx": mobile_base_pos["vx"],
                # "mobile_base_vy": mobile_base_pos["vy"],
                # "mobile_base_vtheta": np.deg2rad(mobile_base_pos["vtheta"]),
                # "neck_roll": np.deg2rad(reachy.joints.neck_roll.present_position),
                # "neck_pitch": np.deg2rad(reachy.joints.neck_pitch.present_position),
                # "neck_yaw": np.deg2rad(reachy.joints.neck_yaw.present_position),
            }
            node.send_output("agent_pos", pa.array(qpos.values()))
