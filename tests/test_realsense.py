import pyrealsense2 as rs
import cv2
import numpy as np

pipe = rs.pipeline()
profile = pipe.start()

try:
  for i in range(0, 100):
    frames = pipe.wait_for_frames()
    color_frame = frames.get_color_frame()
    color_images = np.asanyarray(color_frame.get_data())
    color_images = cv2.cvtColor(color_images, cv2.COLOR_BGR2RGB)
    cv2.imshow("frame", color_images)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
finally:
    pipe.stop()