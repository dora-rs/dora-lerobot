import argparse
import os
import time
from pathlib import Path

import h5py
from pollen_vision.camera_wrappers.depthai import SDKWrapper
from pollen_vision.camera_wrappers.depthai.utils import get_config_file_path
import pyarrow as pa
from dora import Node
import numpy as np

freq = 30

cam_name = "cam_trunk"

cam = SDKWrapper(get_config_file_path("CONFIG_SR"), fps=freq)
# ret, image = cap.read()
time.sleep(1)

# start = time.time()
node = Node()

for event in node:
    # import cv2

    # while True:
    id = event["id"]
    cam_data, _, _ = cam.get_data()

    left_rgb = cam_data["left"]
    # cv2.imshow("frame", left_rgb)
    # if cv2.waitKey(1) & 0xFF == ord("q"):
    # break

    node.send_output("cam_trunk", pa.array(left_rgb.ravel()))
