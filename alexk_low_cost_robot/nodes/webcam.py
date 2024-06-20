"""
LCR webcam: this Dora node reads the webcam feed of CAMERA_ID and propagates in the dataflow.

1. It reads the webcam feed of CAMERA_ID.
2. It sends the webcam feed to the dataflow.
3. If no webcam is found at CAMERA_ID, it sends a black image to the dataflow.

This node also shows the webcam feed in a window.
"""

import os
import cv2

import numpy as np
import pyarrow as pa

from dora import Node


def main():
    if not os.getenv("CAMERA_ID"):
        raise ValueError("Please set the CAMERA_ID environment variable")

    camera_id = os.getenv("CAMERA_ID")

    camera_width = 640
    camera_height = 480

    node = Node()

    if os.name == "nt":
        if not camera_id.isnumeric():
            raise ValueError("You're using Windows, please set the CAMERA_ID environment variable to an integer")

        camera_id = int(camera_id)

    video_capture = cv2.VideoCapture(camera_id)
    font = cv2.FONT_HERSHEY_SIMPLEX

    for event in node:
        event_type = event["type"]

        if event_type == "INPUT":
            event_id = event["id"]

            if event_id == "tick":
                ret, frame = video_capture.read()

                if not ret:
                    frame = np.zeros((camera_height, camera_width, 3), dtype=np.uint8)
                    cv2.putText(
                        frame,
                        "No Webcam was found at index %s" % camera_id,
                        (int(30), int(30)),
                        font,
                        0.75,
                        (255, 255, 255),
                        2,
                        1,
                    )

                node.send_output(
                    "image",
                    pa.array(frame.ravel()),
                    event["metadata"],
                )

                cv2.imshow(str(camera_id), frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        elif event_type == "STOP":
            break
        elif event_type == "ERROR":
            print("[lcr_webcam] error: ", event["error"])
            break

    video_capture.release()


if __name__ == "__main__":
    main()
