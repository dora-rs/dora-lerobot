"""
Dynamixel Client: This node is used to represent a chain of dynamixel motors. It can be used to read positions,
velocities, currents, and set goal positions and currents.
"""

import os
import argparse

import numpy as np
import pyarrow as pa

from dora import Node

from dynamixel import DynamixelXLMotorsChain, TorqueMode


def convert_to_chain_command(values: np.array, ids: np.array) -> (list[int], np.array):
    """
    Convert the values to a chain command. Skip the None values and return the ids and values.
    Args:
        values: np.array
        ids: np.array

    Returns:
        (ids, values): list[int], np.array
    """

    non_none_values = np.array([value for value in values if value is not None])
    non_none_values_ids = [ids[i] for i, value in enumerate(values) if value is not None]

    return non_none_values_ids, non_none_values


def i32_to_u32(value: np.array) -> np.array:
    """
    Convert a signed 32-bit integer array to an unsigned 32-bit integer array.
    Args:
        value: np.array

    Returns:
        np.array
    """

    for i in range(len(value)):
        if value[i] is not None and value[i] < 0:
            value[i] = value[i] + 4294967296

    return value


def u32_to_i32(value: np.array) -> np.array:
    """
    Convert an unsigned 32-bit integer array to a signed 32-bit integer array.
    Args:
        value: np.array

    Returns:
        np.array
    """

    for i in range(len(value)):
        if value[i] is not None and value[i] > 2147483647:
            value[i] = value[i] - 4294967296

    return value


def apply_homing_offset(values: np.array, homing_offset: np.array) -> np.array:
    """
    Apply the homing offset to the values.
    """

    values = u32_to_i32(values)

    for i in range(len(values)):
        if values[i] is not None:
            values[i] += homing_offset[i]

    return i32_to_u32(values)


def apply_inverted(values: np.array, inverted: np.array) -> np.array:
    """
    Apply the inverted values.
    """

    values = u32_to_i32(values)

    for i in range(len(values)):
        if values[i] is not None and inverted[i]:
            values[i] = -values[i]

    return i32_to_u32(values)


def apply_configuration(values: np.array, homing_offset: np.array, inverted: np.array) -> np.array:
    """
    Get the working position of the robot
    Args:
        values: 
        homing_offset: 
        inverted: 

    Returns:

    """

    return apply_homing_offset(apply_inverted(values, inverted), homing_offset)


def invert_configuration(values: np.array, homing_offset: np.array, inverted: np.array) -> np.array:
    """
    Transform working position into real position for the robot.
    Args:
        values: 
        homing_offset: 
        inverted: 

    Returns:

    """

    return apply_inverted(apply_homing_offset(values, np.array([
        -offset if offset is not None else None for offset in homing_offset
    ])), inverted)


class Client:

    def __init__(self, config):
        self.config = config
        self.chain = DynamixelXLMotorsChain(config["port"], config["ids"])

        self.homing_offset = config["homing_offset"]
        self.inverted = config["inverted"]

        # Set initial values

        try:
            self.chain.sync_write_torque_enable(config["torque"])
        except Exception as e:
            print("Error writing torque status:", e)

        try:
            position = self.chain.sync_read_present_position()
            positions = invert_configuration(i32_to_u32(config["initial_goal_position"]), self.homing_offset,
                                             self.inverted)

            ids, positions = convert_to_chain_command(positions, self.chain.motor_ids)

            self.chain.sync_write_goal_position(positions, ids)
        except Exception as e:
            print("Error writing goal position:", e)

        try:
            ids, currents = convert_to_chain_command(config["initial_goal_current"], self.chain.motor_ids)
            self.chain.sync_write_goal_current(currents, ids)
        except Exception as e:
            print("Error writing goal current:", e)

        # Create node and connect it to dataflow (if dynamic)

        self.node = Node(config["name"])

        self.ping_present_position(self.node, None)

    def run(self):
        # Run the event loop of Dora and call appropriate functions

        for event in self.node:
            event_type = event["type"]

            if event_type == "INPUT":
                event_id = event["id"]

                if event_id == "ping_present_position":
                    self.ping_present_position(self.node, event["metadata"])
                elif event_id == "ping_goal_position":
                    self.ping_goal_position(self.node, event["metadata"])
                elif event_id == "ping_present_velocity":
                    self.ping_present_velocity(self.node, event["metadata"])
                elif event_id == "goal_position":
                    self.set_goal_position(event["value"])

            elif event_type == "STOP":
                break
            elif event_type == "ERROR":
                raise ValueError("An error occurred in the dataflow: " + event["error"])

    def close(self):
        self.chain.sync_write_torque_enable(TorqueMode.DISABLED.value)
        self.chain.close()

    def ping_present_position(self, node, metadata):
        try:
            position = apply_configuration(self.chain.sync_read_present_position(),
                                           self.homing_offset,
                                           self.inverted)

            node.send_output(
                "present_position",
                pa.array(position.ravel()),
                metadata
            )

        except ConnectionError as e:
            print("Error reading position:", e)

    def ping_goal_position(self, node, metadata):
        try:
            goal_position = apply_configuration(self.chain.sync_read_goal_position(),
                                                self.homing_offset,
                                                self.inverted)

            node.send_output(
                "goal_position",
                pa.array(goal_position.ravel()),
                metadata
            )
        except ConnectionError as e:
            print("Error reading goal position:", e)

    def ping_present_velocity(self, node, metadata):
        try:
            velocity = self.chain.sync_read_present_velocity()

            node.send_output(
                "present_velocity",
                pa.array(velocity.ravel()),
                metadata
            )
        except ConnectionError as e:
            print("Error reading velocity:", e)

    def set_goal_position(self, goal_position):
        try:
            positions = invert_configuration(goal_position.to_numpy().copy(),
                                             self.homing_offset,
                                             self.inverted)

            ids, positions = convert_to_chain_command(positions, self.chain.motor_ids)

            self.chain.sync_write_goal_position(positions, ids)
        except ConnectionError as e:
            print("Error writing goal position:", e)


def main():
    # Handle dynamic nodes, ask for the name of the node in the dataflow
    parser = argparse.ArgumentParser(
        description="Dynamixel Client: This node is used to represent a chain of dynamixel motors. "
                    "It can be used to read "
                    "positions, velocities, currents, and set goal positions and currents.")

    parser.add_argument("--name", type=str, required=False, help="The name of the node in the dataflow.",
                        default="dynamixel_client")

    args = parser.parse_args()

    # Check if port is set
    if not os.environ.get("PORT"):
        raise ValueError("The port is not set. Please set the port of the dynamixel motors.")

    # Create configuration
    config = {
        "name": args.name,
        "port": os.environ.get("PORT"),  # (e.g. "/dev/ttyUSB0", "COM3")
        "ids": list(map(int, os.environ.get("IDS", "1 2 3 4 5 6").split())),
        "torque": [1 if value == "True" else 0 for value in
                   list(os.getenv("TORQUE", "True True True True True True").split())],

        "initial_goal_position": [int(value) if 'None' not in value else None for value in
                                  list(os.getenv("INITIAL_GOAL_POSITION", "None None None None None None").split())],
        "initial_goal_current": [int(value) if 'None' not in value else None for value in
                                 list(os.getenv("INITIAL_GOAL_CURRENT", "None None None None None None").split())],

        "homing_offset": list(map(int, os.environ.get("HOMING_OFFSET", "0, 0, 0, 0, 0, 0").split())),
        "inverted": [True if value == "True" else False for value in
                     list(os.getenv("INVERTED", "False False False False False False").split())]
    }

    print("Dynamixel Client Configuration: ", config, flush=True)

    client = Client(config)
    client.run()
    client.close()


if __name__ == '__main__':
    main()
