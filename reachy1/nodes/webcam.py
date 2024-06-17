#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import numpy as np
import cv2
import pyarrow as pa

from dora import Node

node = Node()

CAMERA_ID = int(os.getenv("CAMERA_ID", 0))
CAMERA_WIDTH = 480
CAMERA_HEIGHT = 640
video_capture = cv2.VideoCapture(CAMERA_ID)
font = cv2.FONT_HERSHEY_SIMPLEX


for event in node:
    event_type = event["type"]
    if event_type == "INPUT":
        ret, frame = video_capture.read()
        if not ret:
            frame = np.zeros((CAMERA_HEIGHT, CAMERA_WIDTH, 3), dtype=np.uint8)
            cv2.putText(
                frame,
                "No Webcam was found at index %d" % (CAMERA_ID),
                (int(30), int(30)),
                font,
                0.75,
                (255, 255, 255),
                2,
                1,
            )

        # Resize image
        frame = cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        node.send_output(
            "cam_trunk",
            pa.array(frame.ravel()),
            event["metadata"],
        )
        cv2.imshow(str(CAMERA_ID), frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
video_capture.release()
