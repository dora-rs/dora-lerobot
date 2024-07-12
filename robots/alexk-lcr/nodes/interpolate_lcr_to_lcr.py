"""
Interpolate LCR Node: This Dora node is used to calculates appropriate goal positions for the LCR knowing a Leader position
and Follower position
"""
import os
import argparse
import json

import numpy as np
import pyarrow as pa

from dora import Node

from common.position_control import logical_to_physical, physical_to_logical, turn_offset


def calculate_goal_position(physical_position: np.array, logical_position: np.array, physical_to_logical_table: [{}],
                            logical_to_physical_table: [{}]):
    offset = turn_offset(physical_position, physical_to_logical_table, logical_to_physical_table)
    physical = logical_to_physical(logical_position, logical_to_physical_table)

    return np.array([
        physical[i] + offset[i] if physical[i] is not None and offset[i] is not None else None
        for i in range(len(physical))
    ])


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

    node = Node("lcr_interpolate")

    follower_position = np.array([0, 0, 0, 0, 0, 0])

    leader_initialized = False

    for event in node:
        event_type = event["type"]

        if event_type == "INPUT":
            event_id = event["id"]

            if event_id == "leader_position":
                leader_position = event["value"][0]["positions"].values.to_numpy()
                leader_joints = event["value"][0]["joints"].values.to_numpy(zero_copy_only=False)

                leader_physical_to_logical = [
                    leader_control[joint]["physical_to_logical"]
                    for joint in leader_joints
                ]

                leader_logical_to_physical = [
                    leader_control[joint]["logical_to_physical"]
                    for joint in leader_joints
                ]

                if not leader_initialized:
                    leader_initialized = True

                    initial_goal = [
                        leader_control[joint]["initial_goal_position"]
                        for joint in leader_joints
                    ]

                    goal_position = calculate_goal_position(leader_position, initial_goal, leader_physical_to_logical,
                                                            leader_logical_to_physical)
                    goal_position_with_joints = {
                        "joints": [
                            leader_joints[i]
                            for i in range(len(leader_joints)) if goal_position[i] is not None
                        ],
                        "positions": np.array([
                            goal_position[i]
                            for i in range(len(leader_joints)) if goal_position[i] is not None
                        ])
                    }

                    node.send_output(
                        "leader_goal",
                        pa.array([goal_position_with_joints]),
                        event["metadata"]
                    )

                # Convert leader position to logical coordinates
                leader_offset = turn_offset(leader_position, leader_physical_to_logical, leader_logical_to_physical)
                leader_position = physical_to_logical(leader_position, leader_physical_to_logical) - leader_offset

                print("Leader Position: ", leader_position)

                follower_physical_to_logical = [
                    follower_control[joint]["physical_to_logical"]
                    for joint in leader_joints
                ]

                follower_logical_to_physical = [
                    follower_control[joint]["logical_to_physical"]
                    for joint in leader_joints
                ]

                goal_position = calculate_goal_position(follower_position, leader_position,
                                                        follower_physical_to_logical,
                                                        follower_logical_to_physical)

                goal_position_with_joints = {
                    "joints": leader_joints,
                    "positions": goal_position
                }

                node.send_output(
                    "follower_goal",
                    pa.array([goal_position_with_joints]),
                    event["metadata"]
                )
                """
                """

            elif event_id == "follower_position":
                follower_position = event["value"][0]["positions"].values.to_numpy()
        elif event_type == "STOP":
            break
        elif event_type == "ERROR":
            print("[lcr_interpolate] error: ", event["error"])
            break


if __name__ == "__main__":
    main()
