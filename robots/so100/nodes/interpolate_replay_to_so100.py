"""
Interpolate LCR Node: This Dora node is used to calculates appropriate goal positions for the LCR knowing a Leader position
and Follower position
"""
import os
import argparse
import json
import time

import pyarrow as pa
import pyarrow.compute as pc

from dora import Node

from position_control.utils import logical_to_physical, physical_to_logical, compute_goal_with_offset, ARROW_PWM_VALUES
from position_control.configure import build_logical_to_physical, build_physical_to_logical


def main():
    # Handle dynamic nodes, ask for the name of the node in the dataflow
    parser = argparse.ArgumentParser(
        description="Interpolation LCR Node: This Dora node is used to calculates appropriate goal positions for the "
                    "LCR followers knowing a Leader position and Follower position.")

    parser.add_argument("--name", type=str, required=False, help="The name of the node in the dataflow.",
                        default="replay-to-so100")
    parser.add_argument("--follower-control", type=str, help="The configuration file for controlling the follower.",
                        default=None)

    args = parser.parse_args()

    if not os.environ.get("FOLLOWER_CONTROL") and args.follower_control is None:
        raise ValueError(
            "The follower control is not set. Please set the configuration of the follower in the environment "
            "variables or as an argument.")

    with open(os.environ.get("FOLLOWER_CONTROL") if args.follower_control is None else args.follower_control) as file:
        follower_control = json.load(file)

    for joint in follower_control.keys():
        follower_control[joint]["physical_to_logical"] = build_physical_to_logical(
            follower_control[joint]["physical_to_logical"])
        follower_control[joint]["logical_to_physical"] = build_logical_to_physical(
            follower_control[joint]["logical_to_physical"])

    node = Node(args.name)

    follower_initialized = False

    follower_position = pa.scalar({}, type=ARROW_PWM_VALUES)

    for event in node:
        event_type = event["type"]

        if event_type == "INPUT":
            event_id = event["id"]

            if event_id == "leader_position":
                leader_position = event["value"][0]

                if not follower_initialized:
                    continue

                physical_goal = compute_goal_with_offset(follower_position, leader_position, follower_control)

                node.send_output(
                    "follower_goal",
                    pa.array([physical_goal]),
                    event["metadata"]
                )

            elif event_id == "follower_position":
                follower_position = event["value"][0]
                follower_initialized = True

        elif event_type == "ERROR":
            print("[lcr-to-lcr] error: ", event["error"])
            break


if __name__ == "__main__":
    main()
