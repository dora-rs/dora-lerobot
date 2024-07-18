"""
Dynamixel Client: This node is used to represent a chain of dynamixel motors. It can be used to read positions,
velocities, currents, and set goal positions and currents.
"""

import os
import time
import argparse
import json

import pyarrow as pa

from dora import Node

from .bus import DynamixelBus, TorqueMode


class Client:

    def __init__(self, config: dict[str, any]):
        self.config = config

        description = {}
        for i in range(len(config["ids"])):
            description[config["joints"][i]] = (config["ids"][i], config["models"][i])

        self.bus = DynamixelBus(config["port"], description)

        # Set client configuration values, raise errors if the values are not set to indicate that the motors are not
        # configured correctly

        self.bus.write_torque_enable(config["torque"], self.config["joints"])
        self.bus.write_goal_current(config["goal_current"], self.config["joints"])

        time.sleep(0.1)
        self.bus.write_position_d_gain(config["D"], self.config["joints"])
        time.sleep(0.1)
        self.bus.write_position_i_gain(config["I"], self.config["joints"])
        time.sleep(0.1)
        self.bus.write_position_p_gain(config["P"], self.config["joints"])

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

            elif event_type == "ERROR":
                raise ValueError("An error occurred in the dataflow: " + event["error"])

    def close(self):
        self.bus.write_torque_enable(TorqueMode.DISABLED, self.config["joints"])

    def pull_position(self, node, metadata):
        try:
            node.send_output(
                "position",
                pa.array([self.bus.read_position(self.config["joints"])]),
                metadata
            )

        except ConnectionError as e:
            print("Error reading position:", e)

    def pull_velocity(self, node, metadata):
        try:
            node.send_output(
                "velocity",
                pa.array([self.bus.read_velocity(self.config["joints"])]),
                metadata
            )
        except ConnectionError as e:
            print("Error reading velocity:", e)

    def pull_current(self, node, metadata):
        try:
            node.send_output(
                "current",
                pa.array([self.bus.read_current(self.config["joints"])]),
                metadata
            )
        except ConnectionError as e:
            print("Error reading current:", e)

    def write_goal_position(self, goal_position: pa.Array):
        try:
            joints = goal_position[0]["joints"].values
            goal_position = goal_position[0]["values"].values

            self.bus.write_goal_position(goal_position, joints)
        except ConnectionError as e:
            print("Error writing goal position:", e)

    def write_goal_current(self, goal_current: pa.Array):
        try:
            joints = goal_current[0]["joints"].values
            goal_current = goal_current[0]["values"].values

            self.bus.write_goal_current(goal_current, joints)
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
        config = json.load(file)

    joints = config.keys()

    # Create configuration
    bus = {
        "name": args.name,
        "port": port,  # (e.g. "/dev/ttyUSB0", "COM3")
        "ids": [config[joint]["id"] for joint in joints],
        "joints": pa.array(joints, pa.string()),
        "models": [config[joint]["model"] for joint in joints],

        "torque": [TorqueMode.ENABLED if config[joint]["torque"] else TorqueMode.DISABLED for joint in joints],

        "goal_current": pa.array(
            [pa.scalar(config[joint]["goal_current"], pa.uint32()) if config[joint][
                                                                          "goal_current"] is not None else None for
             joint in joints]),

        "P": pa.array([config[joint]["P"] for joint in joints], type=pa.int32()),
        "I": pa.array([config[joint]["I"] for joint in joints], type=pa.int32()),
        "D": pa.array([config[joint]["D"] for joint in joints], type=pa.int32())
    }

    print("Dynamixel Client Configuration: ", bus, flush=True)

    client = Client(bus)
    client.run()
    client.close()


if __name__ == '__main__':
    main()
