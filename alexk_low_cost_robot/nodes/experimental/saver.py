#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import numpy as np
import cv2
import pyarrow as pa
from pathlib import Path
from dora import Node
import subprocess

node = Node()

CAMERA_NAME = os.getenv("CAMERA_NAME", "camera")
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
FPS = 30

def fname(episode):
    return f"{CAMERA_NAME}_episode_{episode:06d}"

i = 0
episode = -1
dataflow_id = node.dataflow_id()

BASE = Path("out") / dataflow_id / "videos"
out_dir = BASE / fname(episode)

for event in node:
    event_type = event["type"]
    if event_type == "INPUT":
        if event["id"] == "record_episode":
            new_episode = event["value"].to_numpy()[0]
            if episode != -1:
                print(f"Storing episode {episode}", flush=True)
                out_dir = BASE / fname(episode)
                # Save video
                ffmpeg_cmd = (
                    f"ffmpeg -r {FPS} "
                    "-f image2 "
                    "-loglevel error "
                    f"-i {str(out_dir / 'frame_%06d.png')} "
                    "-vcodec libx264 "
                    "-g 2 "
                    "-pix_fmt yuv444p "
                    f"{str(out_dir)}.mp4 &&"
                    f"rm -r {str(out_dir)}"
                )
                print(ffmpeg_cmd, flush=True)
                subprocess.Popen([ffmpeg_cmd], start_new_session=True, shell=True)

            if new_episode == -1:
                print("No recording", flush=True)
                episode = -1
                continue
            else:
                episode = new_episode  # Record the next episode
                print(f"Recording episode {episode}", flush=True)
                out_dir = BASE / fname(episode) # Create new directory
                out_dir.mkdir(parents=True, exist_ok=True)
                i = 0

        elif event["id"] == "image":
            # Only record image when in episode.
            if episode == -1:
                continue

            node.send_output(
                "saved_image",
                pa.array([{"path": f"videos/{fname(episode)}.mp4", "timestamp": i / FPS}]),
                event["metadata"],
            )
            image = event["value"].to_numpy().reshape((CAMERA_HEIGHT, CAMERA_WIDTH, 3))
            path = str(out_dir / f"frame_{i:06d}.png")
            cv2.imwrite(path, image)
            i += 1