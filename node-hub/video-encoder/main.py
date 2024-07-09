"""
LCR webcam: this Dora node reads the webcam feed of CAMERA_ID and propagates in the dataflow.

1. It reads the webcam feed of CAMERA_ID.
2. It sends the webcam feed to the dataflow.
3. If no camera is found at CAMERA_ID, it sends a black image to the dataflow.

This node also shows the webcam feed in a window.
"""
import os
import subprocess
import time
from pathlib import Path

import cv2
import argparse

import numpy as np
import pyarrow as pa

from dora import Node
from ffmpeg import FFmpeg


def main():
    # Handle dynamic nodes, ask for the name of the node in the dataflow
    parser = argparse.ArgumentParser(
        description="Video Encoder: This node is used to record episodes of a robot interacting with the environment."
    )

    parser.add_argument("--name", type=str, required=False, help="The name of the node in the dataflow.",
                        default="video_encoder")

    if not os.getenv("VIDEO_NAME") or not os.getenv("FPS"):
        raise ValueError("Please set the VIDEO_NAME and FPS environment variables.")

    if not os.getenv("VIDEO_WIDTH") or not os.getenv("VIDEO_HEIGHT"):
        raise ValueError("Please set the VIDEO_WIDTH and VIDEO_HEIGHT environment variables.")

    video_name = os.getenv("VIDEO_NAME")
    fps = int(os.getenv("FPS"))

    video_width = int(os.getenv("VIDEO_WIDTH"))
    video_height = int(os.getenv("VIDEO_HEIGHT"))

    args = parser.parse_args()

    node = Node(args.name)

    recording = False
    episode_index = 1

    dataflow_id = node.dataflow_id()

    base = Path("out") / dataflow_id / "videos"
    out_dir = base / f"{video_name}_episode_{episode_index:06d}"
    name = f"{video_name}_episode_{episode_index:06d}.mp4"

    if not out_dir.exists():
        out_dir.mkdir(parents=True)

    # We initialize the output canal with a first data
    node.send_output(
        "image",
        pa.array([{"path": f"videos/{name}", "timestamp": float(0) / fps}]),
    )

    frame_count = 0
    for event in node:
        event_type = event["type"]

        if event_type == "INPUT":
            event_id = event["id"]

            if event_id == "image":
                if recording:
                    base = Path("out") / dataflow_id / "videos"
                    out_dir = base / f"{video_name}_episode_{episode_index:06d}"
                    name = f"{video_name}_episode_{episode_index:06d}.mp4"

                    if not out_dir.exists():
                        out_dir.mkdir(parents=True)

                    node.send_output(
                        "image",
                        pa.array([{"path": f"videos/{name}", "timestamp": float(frame_count) / fps}]),
                        event["metadata"],
                    )

                    image = event["value"].to_numpy().reshape((video_height, video_width, 3))
                    path = str(out_dir / f"frame_{frame_count:06d}.png")
                    cv2.imwrite(path, image)

                    frame_count += 1

            elif event_id == "episode_index":
                episode = event["value"][0].as_py()
                recording = episode != -1

                if recording:
                    episode_index = episode
                else:
                    # save all the frames into a video
                    base = Path("out") / dataflow_id / "videos"
                    out_dir = base / f"{video_name}_episode_{episode_index:06d}"
                    name = f"{video_name}_episode_{episode_index:06d}.mp4"
                    video_path = base / name

                    ffmpeg = (
                        FFmpeg()
                        .option("y")
                        .input(str(out_dir / "frame_%06d.png"), f='image2', r=fps)
                        .output(str(video_path), vcodec='libx264', g=2, pix_fmt='yuv444p')
                    )

                    ffmpeg.execute()

                    frame_count = 0

        elif event_type == "STOP":
            break
        elif event_type == "ERROR":
            raise ValueError("An error occurred in the dataflow: " + event["error"])


if __name__ == "__main__":
    main()