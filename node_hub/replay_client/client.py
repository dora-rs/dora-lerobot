"""
Dynamixel Client: This node is used to represent a chain of dynamixel motors. It can be used to read positions,
velocities, currents, and set goal positions and currents.
"""

import os
import time
import argparse

import numpy as np
import pyarrow as pa
import pandas as pd

from dora import Node


class Client:

    def __init__(self, config: dict[str, any]):
        self.config = config

        self.node = Node(config["name"])

        action_file = pd.read_parquet(config["episode_path"] + "/action.parquet")
        episode_file = pd.read_parquet(config["episode_path"] + "/episode_index.parquet")

        # find in episode_file, the row with value of [config["episode_id"]]
        episode = episode_file[episode_file["episode_index"] == config["episode_id"]]

        # find in episode_file the next row after the episode_id
        next_episode = episode_file[episode_file.index > episode.index[0]].head(1)

        # deduce the start and end index of the action file thanks to "timestamp_utc" column
        start_timestamp = episode["timestamp_utc"].iloc[0]
        end_timestamp = next_episode["timestamp_utc"].iloc[0]

        # filter action file that are between start and end timestamp
        self.action = action_file[
            (action_file["timestamp_utc"] >= start_timestamp) & (action_file["timestamp_utc"] < end_timestamp)]

        self.frame = 0

    def run(self):
        for event in self.node:
            event_type = event["type"]

            if event_type == "INPUT":
                event_id = event["id"]

                if event_id == "pull_position":
                    if self.pull_position(self.node, event["metadata"]):
                        break
                elif event_id == "end":
                    break

            elif event_type == "STOP":
                break
            elif event_type == "ERROR":
                raise ValueError("An error occurred in the dataflow: " + event["error"])

    def pull_position(self, node, metadata) -> bool:
        if self.frame >= len(self.action):
            return True

        action = self.action.iloc[self.frame]
        self.frame += 1

        node.send_output("position", pa.array(action["action"]), metadata)


def main():
    # Handle dynamic nodes, ask for the name of the node in the dataflow
    parser = argparse.ArgumentParser(
        description="Replay Client: This node is used to replay a sequence of goals for a followee robot.")

    parser.add_argument("--name", type=str, required=False, help="The name of the node in the dataflow.",
                        default="replay_client")

    args = parser.parse_args()

    if not os.getenv("PATH") or not os.getenv("EPISODE"):
        raise ValueError("The environment variables PATH and EPISODE_ID must be set.")

    if not isinstance(int(os.getenv("EPISODE")), int):
        raise ValueError("The environment variable EPISODE_ID must be an integer.")

    # Create configuration
    config = {
        "name": args.name,
        "episode_path": os.getenv("PATH"),
        "episode_id": int(os.getenv("EPISODE"))
    }

    print("Replay Client Configuration: ", config, flush=True)

    client = Client(config)
    client.run()


if __name__ == '__main__':
    main()
