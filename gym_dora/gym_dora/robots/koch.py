"""
Configurations of Alexander Koch single arm

From "Low-Cost Robot Arm by Tau Robotics"
https://github.com/AlexanderKoch-Koch/low_cost_robot
"""

FPS = 50

ACTIONS = [
    # position and quaternion for end effector
    "waist",
    "shoulder",
    "elbow",
    "wrist",
    # normalized gripper position (0: close, 1: open)
    "gripper",
]


JOINTS = [
    # absolute joint position
    "waist",
    "shoulder",
    "elbow",
    "wrist",
    # normalized gripper position 0: close, 1: open
    "gripper",
]

CAMERAS = {
    # tested with Intel(R) RealSense D455 (no depth)
    "cam_high": (480, 640, 3),
    # tested with C922 Pro Stream Webcam
    "cam_low": (480, 640, 3),
}
