"""
Interpolate LCR Node: This Dora node is used to calculates appropriate goal positions for the LCR knowing a Leader position
and Follower position
"""
import os
import argparse
import json
import time

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc

from dora import Node

from common.position_control.utils import logical_to_physical, physical_to_logical
from common.position_control.configure import build_logical_to_physical, build_physical_to_logical


def main():
    # Handle dynamic nodes, ask for the name of the node in the dataflow
    parser = argparse.ArgumentParser(
        description="Interpolation LCR Node: This Dora node is used to calculates appropriate goal positions for the "
                    "LCR followers knowing a Leader position and Follower position.")

    parser.add_argument("--name", type=str, required=False, help="The name of the node in the dataflow.",
                        default="lcr-to-simu-lcr")
    parser.add_argument("--leader-control", type=str, help="The configuration file for controlling the leader.",
                        default=None)

    args = parser.parse_args()

    # Check if leader-control is set
    if not os.environ.get("LEADER_CONTROL") and args.leader_control is None:
        raise ValueError(
            "The leader control is not set. Please set the configuration of the leader in the environment variables or "
            "as an argument.")

    with open(os.environ.get("LEADER_CONTROL") if args.leader_control is None else args.leader_control) as file:
        leader_control = json.load(file)

    for joint in leader_control.keys():
        leader_control[joint]["physical_to_logical"] = build_physical_to_logical(
            leader_control[joint]["physical_to_logical"])
        leader_control[joint]["logical_to_physical"] = build_logical_to_physical(
            leader_control[joint]["logical_to_physical"])

    logical_leader_goal = pa.scalar({
        "joints": pa.array(leader_control.keys(), type=pa.string()),
        "positions": pa.array([leader_control[joint]["goal_position"] for joint in leader_control.keys()],
                              type=pa.float32())
    }, type=pa.struct({
        "joints": pa.list_(pa.string()),
        "positions": pa.list_(pa.float32())
    }))

    node = Node(args.name)

    for event in node:
        event_type = event["type"]

        if event_type == "INPUT":
            event_id = event["id"]

            if event_id == "leader_position":
                leader_position = event["value"][0]
                leader_position = physical_to_logical(leader_position, leader_control)

                follower_goal = pa.scalar({
                    "joints": [joint.as_py() + "_joint"
                               for joint in leader_position["joints"].values],
                    "positions": pc.multiply(
                        pc.add(leader_position["positions"].values, pa.array([0, 0, 0, 0, 90, 0], type=pa.float32())),
                        pa.array(
                            [np.pi / 180, np.pi / 180, np.pi / 180, np.pi / 180, np.pi / 180,
                             np.pi / 180 * 700 / 450],
                            type=pa.float32()))
                }, type=pa.struct({
                    "joints": pa.list_(pa.string()),
                    "positions": pa.list_(pa.float32())
                }))

                node.send_output(
                    "follower_goal",
                    pa.array([follower_goal]),
                    event["metadata"]
                )

        elif event_type == "STOP":
            break
        elif event_type == "ERROR":
            print("[lcr_interpolate] error: ", event["error"])
            break


if __name__ == "__main__":
    main()
