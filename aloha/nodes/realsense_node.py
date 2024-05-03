import pyrealsense2 as rs
import numpy as np
from dora import Node
import pyarrow as pa
import os

IMAGE_WIDTH = int(os.getenv("IMAGE_WIDTH", "1280"))
IMAGE_HEIGHT = int(os.getenv("IMAGE_HEIGHT", "720"))
pipe = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, IMAGE_WIDTH, IMAGE_HEIGHT, rs.format.bgr8, 15)
profile = pipe.start(config)

node = Node()

for event in node:
    frames = pipe.wait_for_frames()
    color_frame = frames.get_color_frame()
    color_images = np.asanyarray(color_frame.get_data())
    node.send_output("image", pa.array(color_images.ravel()))
