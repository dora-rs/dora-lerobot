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

from common.position_control import logical_to_physical, physical_to_logical, calculate_offset


def main():
    # Handle dynamic nodes, ask for the name of the node in the dataflow
    parser = argparse.ArgumentParser(
        description="Interpolation LCR Node: This Dora node is used to calculates appropriate goal positions for the "
                    "LCR followers knowing a Leader position and Follower position.")

    parser.add_argument("--name", type=str, required=False, help="The name of the node in the dataflow.",
                        default="lcr-to-lcr")
    parser.add_argument("--leader-control", type=str, help="The configuration file for controlling the leader.",
                        default=None)
    parser.add_argument("--follower-control", type=str, help="The configuration file for controlling the follower.",
                        default=None)

    args = parser.parse_args()

    # Check if leader-control and follower-control are set
    if not os.environ.get("LEADER_CONTROL") and args.leader_control is None:
        raise ValueError(
            "The leader control is not set. Please set the configuration of the leader in the environment variables or "
            "as an argument.")

    if not os.environ.get("FOLLOWER_CONTROL") and args.follower_control is None:
        raise ValueError(
            "The follower control is not set. Please set the configuration of the follower in the environment "
            "variables or as an argument.")

    with open(os.environ.get("LEADER_CONTROL") if args.leader_control is None else args.leader_control) as file:
        leader_control = json.load(file)

    with open(os.environ.get("FOLLOWER_CONTROL") if args.follower_control is None else args.follower_control) as file:
        follower_control = json.load(file)

    node = Node("lcr-to-lcr")

    follower_position = pa.scalar({}, type=pa.struct({
        "joints": pa.list_(pa.string()),
        "positions": pa.list_(pa.int32())
    }))

    leader_position = pa.scalar({}, type=pa.struct({
        "joints": pa.list_(pa.string()),
        "positions": pa.list_(pa.int32())
    }))

    for event in node:
        event_type = event["type"]

        if event_type == "INPUT":
            event_id = event["id"]

            if event_id == "leader_position":
                leader_position = event["value"][0]

                leader_position = physical_to_logical(leader_position, leader_control)

                leader_position = pa.scalar({
                    "joints": leader_position["joints"].values,
                    "positions": pa.array(pc.floor(pc.multiply(leader_position["positions"].values,
                                                               pa.array([1, 1, 1, 1, 1, 700 / 450],
                                                                        type=pa.float32()))),
                                          type=pa.int32())
                }, type=pa.struct({
                    "joints": pa.list_(pa.string()),
                    "positions": pa.list_(pa.int32())
                }))

                node.send_output(
                    "logical_goal",
                    pa.array([leader_position]),
                    event["metadata"]
                )

            elif event_id == "follower_position":
                follower_position = event["value"][0]

                follower_position = physical_to_logical(follower_position, follower_control)

                node.send_output(
                    "logical_position",
                    pa.array([follower_position]),
                    event["metadata"]
                )

        elif event_type == "STOP":
            break
        elif event_type == "ERROR":
            print("[lcr-to-lcr] error: ", event["error"])
            break


if __name__ == "__main__":
    main()
