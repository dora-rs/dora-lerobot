import cv2
import time

import pyarrow as pa
from dora import Node

# import h5py

freq = 30

cam_name = "cam_trunk"


from reachy_sdk import ReachySDK

ROBOT_IP = "10.42.0.24"
reachy = ReachySDK(ROBOT_IP)


node = Node()
index = 0


for event in node:
    # import cv2

    # while True:
    left_rgb = reachy.right_camera.last_frame

    # Convert image to BGR from RGB
    left_rgb = cv2.cvtColor(left_rgb, cv2.COLOR_BGR2RGB)

    node.send_output("cam_trunk", pa.array(left_rgb.ravel()))
