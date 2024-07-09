"""
Dynamixel Client: This node is used to represent a chain of dynamixel motors. It can be used to read positions,
velocities, currents, and set goal positions and currents.
"""

import os
import argparse
import time

import numpy as np
import pyarrow as pa

from dora import Node

import mujoco
import mujoco.viewer


class Client:

    def __init__(self, config: dict[str, any]):
        self.config = config

        self.m = mujoco.MjModel.from_xml_path(filename=config["scene"])
        self.data = mujoco.MjData(self.m)

        self.node = Node(config["name"])

    def run(self):
        with mujoco.viewer.launch_passive(self.m, self.data) as viewer:
            for event in self.node:
                event_type = event["type"]

                if event_type == "INPUT":
                    event_id = event["id"]

                    if event_id == "tick":
                        self.node.send_output(
                            "tick",
                            pa.array([]),
                            event["metadata"]
                        )

                        if not viewer.is_running():
                            break

                        step_start = time.time()

                        # Step the simulation forward
                        mujoco.mj_step(self.m, self.data)
                        viewer.sync()

                        # Rudimentary time keeping, will drift relative to wall clock.
                        time_until_next_step = self.m.opt.timestep - (time.time() - step_start)
                        if time_until_next_step > 0:
                            time.sleep(time_until_next_step)

                    elif event_id == "pull_position":
                        self.pull_position(self.node, event["metadata"])
                    elif event_id == "pull_velocity":
                        self.pull_velocity(self.node, event["metadata"])
                    elif event_id == "pull_current":
                        self.pull_current(self.node, event["metadata"])
                    elif event_id == "write_goal_position":
                        self.write_goal_position(event["value"])
                    elif event_id == "end":
                        break

                elif event_type == "STOP":
                    break
                elif event_type == "ERROR":
                    raise ValueError("An error occurred in the dataflow: " + event["error"])

    def pull_position(self, node, metadata):
        pass

    def pull_velocity(self, node, metadata):
        pass

    def pull_current(self, node, metadata):
        pass

    def write_goal_position(self, goal_position_with_joints):
        joints = goal_position_with_joints[0]["joints"].values.to_numpy(zero_copy_only=False)
        goal_position = goal_position_with_joints[0]["positions"].values.to_numpy()

        for i, joint in enumerate(joints):
            self.data.joint(joint).qpos[0] = goal_position[i]


def main():
    # Handle dynamic nodes, ask for the name of the node in the dataflow
    parser = argparse.ArgumentParser(
        description="MujoCo Client: This node is used to represent a MuJoCo simulation. It can be used instead of a "
                    "follower arm to test the dataflow."
    )

    parser.add_argument("--name", type=str, required=False, help="The name of the node in the dataflow.",
                        default="mujoco_client")

    args = parser.parse_args()

    # Create configuration
    config = {
        "name": args.name,

        "scene": os.environ.get("SCENE", "../assets/simulation/reach_cube.xml"),

        "joints": list(map(str, os.environ.get("JOINTS", "shoulder_pan shoulder_lift elbow_flex wrist_flex wrist_roll "
                                                         "gripper").split())),

        "initial_goal_position": np.array([np.int32(value) if 'None' not in value else None for value in
                                           list(os.getenv("INITIAL_GOAL_POSITION",
                                                          "None None None None None None").split())]),
    }

    print("Mujoco Client Configuration: ", config, flush=True)

    client = Client(config)
    client.run()


if __name__ == '__main__':
    main()
