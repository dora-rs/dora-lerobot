"""
Dynamixel Client: This node is used to represent a chain of dynamixel motors. It can be used to read positions,
velocities, currents, and set goal positions and currents.
"""

import os
import time
import argparse

import numpy as np
import pyarrow as pa

from dora import Node

from dora_lerobot.dynamixel_bus import DynamixelBus, TorqueMode
from dora_lerobot.position_control import DriveMode, logical_to_physical, physical_to_logical


class Client:

    def __init__(self, config: dict[str, any]):
        self.config = config

        description = {}
        for i in range(len(config["ids"])):
            description[config["joints"][i]] = (config["ids"][i], config["models"][i])

        self.bus = DynamixelBus(config["port"], description)

        self.offsets = config["offsets"]
        self.drive_modes = config["drive_modes"]

        # Set initial values

        try:
            self.bus.sync_write_torque_enable(config["torque"], self.config["joints"])
        except Exception as e:
            print("Error writing torque status:", e)

        try:
            positions = logical_to_physical(
                config["initial_goal_position"],
                self.offsets,
                self.drive_modes)

            self.bus.sync_write_goal_position(positions, self.config["joints"])
        except Exception as e:
            print("Error writing goal position:", e)

        try:
            self.bus.sync_write_goal_current(config["initial_goal_current"], self.config["joints"])
        except Exception as e:
            print("Error writing goal current:", e)

        self.node = Node(config["name"])

    def run(self):
        for event in self.node:
            event_type = event["type"]

            if event_type == "INPUT":
                event_id = event["id"]

                if event_id == "pull_position":
                    self.pull_position(self.node, event["metadata"])
                elif event_id == "pull_velocity":
                    self.pull_velocity(self.node, event["metadata"])
                elif event_id == "pull_current":
                    self.pull_current(self.node, event["metadata"])
                elif event_id == "write_goal_position":
                    self.write_goal_position(event["value"])
                elif event_id == "write_goal_current":
                    self.write_goal_current(event["value"])
                elif event_id == "stop":
                    break

            elif event_type == "STOP":
                break
            elif event_type == "ERROR":
                raise ValueError("An error occurred in the dataflow: " + event["error"])

    def close(self):
        self.bus.sync_write_torque_enable(TorqueMode.DISABLED, self.config["joints"])

    def pull_position(self, node, metadata):
        try:
            position = physical_to_logical(
                self.bus.sync_read_position(self.config["joints"]),
                self.offsets,
                self.drive_modes)

            position_with_joints = {
                "joints": self.config["joints"],
                "positions": position
            }

            node.send_output(
                "position",
                pa.array([position_with_joints]),
                metadata
            )

        except ConnectionError as e:
            print("Error reading position:", e)

    def pull_velocity(self, node, metadata):
        try:
            velocity = self.bus.sync_read_velocity(self.config["joints"])

            velocity_with_joints = {
                "joints": self.config["joints"],
                "velocities": velocity
            }

            node.send_output(
                "velocity",
                pa.array([velocity_with_joints]),
                metadata
            )
        except ConnectionError as e:
            print("Error reading velocity:", e)

    def pull_current(self, node, metadata):
        try:
            current = self.bus.sync_read_current(self.config["joints"])

            current_with_joints = {
                "joints": self.config["joints"],
                "currents": current
            }

            node.send_output(
                "current",
                pa.array([current_with_joints]),
                metadata
            )
        except ConnectionError as e:
            print("Error reading current:", e)

    def write_goal_position(self, goal_position_with_joints: {}):
        try:
            joints = goal_position_with_joints[0]["joints"].values.to_numpy(zero_copy_only=False)
            goal_position = goal_position_with_joints[0]["positions"].values.to_numpy()

            self.bus.sync_write_goal_position(logical_to_physical(goal_position, self.offsets, self.drive_modes),
                                              joints)
        except ConnectionError as e:
            print("Error writing goal position:", e)

    def write_goal_current(self, goal_current_with_joints: np.array):
        try:
            joints = goal_current_with_joints[0]["joints"].values.to_numpy(zero_copy_only=False)
            goal_current = goal_current_with_joints[0]["currents"].values.to_numpy()

            self.bus.sync_write_goal_current(goal_current, joints)
        except ConnectionError as e:
            print("Error writing goal current:", e)


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

        "ids": list(map(np.uint8, os.environ.get("IDS", "1 2 3 4 5 6").split())),
        "joints": np.array(
            list(map(str, os.environ.get("JOINTS", "shoulder_pan shoulder_lift elbow_flex wrist_flex wrist_roll "
                                                   "gripper").split()))),
        "models": list(
            map(str, os.environ.get("MODELS", "x_series x_series x_series x_series x_series x_series").split())),

        "torque": np.array([TorqueMode.ENABLED if value == "True" else TorqueMode.DISABLED for value in
                            list(os.getenv("TORQUE", "True True True True True True").split())]),

        "initial_goal_position": np.array([np.int32(value) if 'None' not in value else None for value in
                                           list(os.getenv("INITIAL_GOAL_POSITION",
                                                          "None None None None None None").split())]),
        "initial_goal_current": np.array([np.int32(value) if 'None' not in value else None for value in
                                          list(os.getenv("INITIAL_GOAL_CURRENT",
                                                         "None None None None None None").split())]),

        "offsets": np.array(list(map(np.int32, os.environ.get("OFFSETS", "0, 0, 0, 0, 0, 0").split()))).astype(
            np.int32),
        "drive_modes": np.array(
            [DriveMode.POSITIVE_CURRENT if value == "POS" else DriveMode.NEGATIVE_CURRENT for value in
             list(os.getenv("DRIVE_MODES", "False False False False False False").split())])
    }

    print("Dynamixel Client Configuration: ", config, flush=True)

    client = Client(config)
    client.run()
    client.close()


if __name__ == '__main__':
    main()
