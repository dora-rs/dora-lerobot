"""
Configurations of Aloha/Aloha2 duo arms

From "Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware"
https://tonyzhaozh.github.io/aloha/
and "ALOHA 2: An Enhanced Low-Cost Hardware for Bimanual Teleoperation"
https://aloha-2.github.io
"""

FPS = 30

CAMERAS = {
    "cam_high": (480, 640, 3),
    "cam_low": (480, 640, 3),
    "cam_left_wrist": (480, 640, 3),
    "cam_right_wrist": (480, 640, 3),
}

JOINTS = [
    # absolute joint position
    # "left_arm_waist",
    # "left_arm_shoulder",
    # "left_arm_elbow",
    # "left_arm_forearm_roll",
    # "left_arm_wrist_angle",
    # "left_arm_wrist_rotate",
    # # normalized gripper position 0: close, 1: open
    # "left_arm_gripper",
    # absolute joint position
    "right_arm_waist",
    "right_arm_shoulder",
    "right_arm_elbow",
    "right_arm_forearm_roll",
    "right_arm_wrist_angle",
    "right_arm_wrist_rotate",
    # normalized gripper position 0: close, 1: open
    "right_arm_gripper",
]

ACTIONS = [
    # position and quaternion for end effector
    # "left_arm_waist",
    # "left_arm_shoulder",
    # "left_arm_elbow",
    # "left_arm_forearm_roll",
    # "left_arm_wrist_angle",
    # "left_arm_wrist_rotate",
    # # normalized gripper position (0: close, 1: open)
    # "left_arm_gripper",
    "right_arm_waist",
    "right_arm_shoulder",
    "right_arm_elbow",
    "right_arm_forearm_roll",
    "right_arm_wrist_angle",
    "right_arm_wrist_rotate",
    # normalized gripper position (0: close, 1: open)
    "right_arm_gripper",
]

