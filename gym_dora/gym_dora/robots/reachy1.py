"""
Configurations of Reach v2 humanoid robot on wheels

From Pollen Robotics
https://www.pollen-robotics.com
"""

FPS = 30

ACTIONS = [
    "r_arm_shoulder_pitch",
    "r_arm_shoulder_roll",
    "r_arm_shoulder_yaw",
    "r_arm_elbow_pitch",
    "r_forearm_yaw",
    "r_arm_wrist_pitch",
    "r_arm_wrist_roll",
    "r_gripper",
]


JOINTS = [
    "r_arm_shoulder_pitch",
    "r_arm_shoulder_roll",
    "r_arm_shoulder_yaw",
    "r_arm_elbow_pitch",
    "r_forearm_yaw",
    "r_arm_wrist_pitch",
    "r_arm_wrist_roll",
    "r_gripper",
]

CAMERAS = {
    "cam_trunk": (640, 480, 3),
}
