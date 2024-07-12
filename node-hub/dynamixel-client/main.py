"""
Dynamixel Client: This node is used to represent a chain of dynamixel motors. It can be used to read positions,
velocities, currents, and set goal positions and currents.
"""

import os
import time
import argparse
import json

import numpy as np
import pyarrow as pa

from dora import Node

from common.dynamixel_bus import DynamixelBus, TorqueMode


class Client:

    def __init__(self, config: dict[str, any]):
        self.config = config

        description = {}
        for i in range(len(config["ids"])):
            description[config["joints"][i]] = (config["ids"][i], config["models"][i])

        self.bus = DynamixelBus(config["port"], description)

        # Set initial values

        try:
            self.bus.sync_write_torque_enable(config["torque"], self.config["joints"])
        except Exception as e:
            print("Error writing torque status:", e)

        try:
            self.bus.sync_write_goal_current(config["goal_current"], self.config["joints"])
        except Exception as e:
            print("Error writing goal current:", e)
        time.sleep(0.1)

        try:
            self.bus.sync_write_position_d_gain(config["D"], self.config["joints"])
        except Exception as e:
            print("Error writing gains:", e)
        time.sleep(0.1)

        try:
            self.bus.sync_write_position_i_gain(config["I"], self.config["joints"])
        except Exception as e:
            print("Error writing gains:", e)
        time.sleep(0.1)

        try:
            self.bus.sync_write_position_p_gain(config["P"], self.config["joints"])
        except Exception as e:
            print("Error writing gains:", e)

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
                elif event_id == "end":
                    break

            elif event_type == "STOP":
                break
            elif event_type == "ERROR":
                raise ValueError("An error occurred in the dataflow: " + event["error"])

    def close(self):
        self.bus.sync_write_torque_enable(TorqueMode.DISABLED, self.config["joints"])

    def pull_position(self, node, metadata):
        try:
            position = self.bus.sync_read_position(self.config["joints"])

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

            self.bus.sync_write_goal_position(goal_position, joints)
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
    parser.add_argument("--port", type=str, required=False, help="The port of the dynamixel motors.", default=None)
    parser.add_argument("--config", type=str, help="The configuration of the dynamixel motors.", default=None)

    args = parser.parse_args()

    # Check if port is set
    if not os.environ.get("PORT") and args.port is None:
        raise ValueError(
            "The port is not set. Please set the port of the dynamixel motors in the environment variables or as an "
            "argument.")

    port = os.environ.get("PORT") if args.port is None else args.port

    # Check if config is set
    if not os.environ.get("CONFIG") and args.config is None:
        raise ValueError(
            "The configuration is not set. Please set the configuration of the dynamixel motors in the environment "
            "variables or as an argument.")

    with open(os.environ.get("CONFIG") if args.config is None else args.config) as file:
        config = json.load(file)["config"]

    # Create configuration
    bus = {
        "name": args.name,
        "port": port,  # (e.g. "/dev/ttyUSB0", "COM3")
        "ids": np.array([np.uint8(motor["id"]) for motor in config]),
        "joints": np.array([motor["joint"] for motor in config]),
        "models": np.array([motor["model"] for motor in config]),

        "torque": np.array(
            [TorqueMode.ENABLED if motor["torque"] else TorqueMode.DISABLED for motor in config]),

        "goal_current": np.array(
            [np.uint32(motor["goal_current"]) if motor["goal_current"] is not None else None for motor
             in config]),

        "P": np.array([motor["P"] for motor in config]),
        "I": np.array([motor["I"] for motor in config]),
        "D": np.array([motor["D"] for motor in config])
    }

    print("Dynamixel Client Configuration: ", bus, flush=True)

    client = Client(bus)
    client.run()
    client.close()


if __name__ == '__main__':
    main()
