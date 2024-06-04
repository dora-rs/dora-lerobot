"""
Configurations of Reach v2 humanoid robot on wheels

From Pollen Robotics
https://www.pollen-robotics.com
"""

FPS = 30

ACTIONS = [
    "l_arm_shoulder_pitch",
    "l_arm_shoulder_roll",
    "l_arm_elbow_yaw",
    "l_arm_elbow_pitch",
    "l_arm_wrist_roll",
    "l_arm_wrist_pitch",
    "l_arm_wrist_yaw",
    "l_gripper",
    "r_arm_shoulder_pitch",
    "r_arm_shoulder_roll",
    "r_arm_elbow_yaw",
    "r_arm_elbow_pitch",
    "r_arm_wrist_roll",
    "r_arm_wrist_pitch",
    "r_arm_wrist_yaw",
    "r_gripper",
]


JOINTS = [
    "l_arm_shoulder_pitch",
    "l_arm_shoulder_roll",
    "l_arm_elbow_yaw",
    "l_arm_elbow_pitch",
    "l_arm_wrist_roll",
    "l_arm_wrist_pitch",
    "l_arm_wrist_yaw",
    "l_gripper",
    "r_arm_shoulder_pitch",
    "r_arm_shoulder_roll",
    "r_arm_elbow_yaw",
    "r_arm_elbow_pitch",
    "r_arm_wrist_roll",
    "r_arm_wrist_pitch",
    "r_arm_wrist_yaw",
    "r_gripper",
]

CAMERAS = {
    "cam_trunk": (800, 1280, 3),
}
