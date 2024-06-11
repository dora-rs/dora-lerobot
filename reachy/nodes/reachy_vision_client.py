import time

import cv2
import pyarrow as pa
from dora import Node

# import h5py
from pollen_vision.camera_wrappers.depthai import SDKWrapper
from pollen_vision.camera_wrappers.depthai.utils import get_config_file_path

freq = 30

cam_name = "cam_trunk"

time.sleep(5)
cam = SDKWrapper(get_config_file_path("CONFIG_SR"), fps=freq)


node = Node()
index = 0


for event in node:

    id = event["id"]
    cam_data, _, _ = cam.get_data()

    left_rgb = cam_data["left"]

    # Convert image to BGR from RGB
    left_rgb = cv2.cvtColor(left_rgb, cv2.COLOR_BGR2RGB)
    node.send_output("cam_trunk", pa.array(left_rgb.ravel()))
