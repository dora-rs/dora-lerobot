"""
Dynamixel Client: This node is used to represent a chain of dynamixel motors. It can be used to read positions,
velocities, currents, and set goal positions and currents.
"""

import os
import argparse

import numpy as np
import pyarrow as pa

from dora import Node

from dynamixel import DynamixelXLMotorsChain


def motor_chain_command(values: np.array) -> (list[int], np.array):
    # Only retrieve non-None values
    non_none_values = np.array([value for value in values if value is not None])
    non_none_values_ids = [i + 1 for i, value in enumerate(values) if value is not None]

    return non_none_values_ids, non_none_values


def u32_to_i32(value: np.array) -> np.array:
    for i in range(len(value)):
        if value[i] >= 2147483648:
            value[i] = value[i] - 4294967296

    return value


def i32_to_u32(value: np.array) -> np.array:
    for i in range(len(value)):
        if value[i] < 0:
            value[i] = value[i] + 4294967296

    return value


def in_range_position(value: np.array) -> np.array:
    i32_values = u32_to_i32(value)

    for i in range(len(i32_values)):
        if i32_values[i] > 4096:
            i32_values[i] = i32_values[i] % 4096
        if i32_values[i] < -4096:
            i32_values[i] = -(-i32_values[i] % 4096)

        if i32_values[i] > 2048:
            i32_values[i] = - 2048 + (i32_values[i] % 2048)
        elif i32_values[i] < -2048:
            i32_values[i] = 2048 - (-i32_values[i] % 2048)

    return i32_to_u32(i32_values)


def main():
    # Handle dynamic nodes, ask for the name of the node in the dataflow
    parser = argparse.ArgumentParser(
        description="Dynamixel Client: This node is used to represent a chain of dynamixel motors. "
                    "It can be used to read "
                    "positions, velocities, currents, and set goal positions and currents.")

    parser.add_argument("--name", type=str, required=False, help="The name of the node.", default="dynamixel_client")

    args = parser.parse_args()

    # Retrieve environment variables

    path = os.environ.get("PORT", "COM9")
    ids = list(map(int, os.environ.get("IDS", "1, 2, 3, 4, 5, 6").split()))
    torque_status = list(map(int, os.environ.get("TORQUE", "0, 0, 0, 0, 0, 1").split()))

    print("Path: ", path, flush=True)
    print("IDS: ", ids, flush=True)
    print("Torque status: ", torque_status, flush=True)

    position = list(os.getenv("POSITION", "None, None, None, None, None, None").split())
    position = [int(value) if 'None' not in value else None for value in position]

    print("Position: ", position, flush=True)

    current = list(os.getenv("CURRENT", "None, None, None, None, None, None").split())
    current = [int(value) if value != 'None' and value != ' None' else None for value in current]

    print("Current: ", current, flush=True)

    # Create a DynamixelXLMotorsChain object
    chain = DynamixelXLMotorsChain(path, ids)

    # Initialize values

    try:
        chain.sync_write_torque(torque_status)
    except Exception as e:
        print("Error writing torque status:", e)

    ids, positions = motor_chain_command(position)
    try:
        chain.sync_write_goal_position(i32_to_u32(positions), ids)
    except Exception as e:
        print("Error writing goal position:", e)

    ids, currents = motor_chain_command(current)
    try:
        chain.sync_write_goal_current(currents, ids)
    except Exception as e:
        print("Error writing goal current:", e)

    # Create a Dora node
    node = Node(args.name)

    for event in node:
        event_type = event["type"]

        if event_type == "INPUT":
            event_id = event["id"]

            if event_id == "tick":
                # Read the positions of the chain and send them to the output
                try:
                    position = in_range_position(chain.sync_read_position())

                    node.send_output(
                        "position",
                        pa.array(position.ravel()),
                        event["metadata"],
                    )
                except Exception as e:
                    print("Error reading position:", e)

            if event_id == "goal_position":
                # Set the goal position of the chain

                motor_ids, goal_position = motor_chain_command(event["value"].to_numpy())
                goal_position = u32_to_i32(goal_position)

                try:
                    position = u32_to_i32(chain.sync_read_position())

                    for i in range(len(goal_position)):
                        if position[i] > 0:
                            goal_position[i] = goal_position[i] + (position[i] // 4096) * 4096
                        else:
                            goal_position[i] = goal_position[i] - (-position[i] // 4096) * 4096

                    goal_position = i32_to_u32(goal_position)

                    chain.sync_write_goal_position(goal_position, motor_ids)
                except Exception as e:
                    print("Error writing goal position:", e)

            if event_id == "goal_current":
                # Set the goal current of the chain
                pass
            if event_id == "torque_status":
                # Set the torque status of the chain
                motor_ids, torque_status = motor_chain_command(event["value"].to_numpy())

                try:
                    chain.sync_write_torque(torque_status, motor_ids)
                except Exception as e:
                    print("Error writing torque status:", e)
        elif event_type == "STOP":
            break
        elif event_type == "ERROR":
            raise ValueError("An error occurred in the dataflow: " + event["error"])

    chain.sync_write_torque_disable()
    chain.close()


if __name__ == '__main__':
    main()
