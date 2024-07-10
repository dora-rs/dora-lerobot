"""
Interpolate LCR Node: This Dora node is used to calculates appropriate goal positions for the LCR knowing a Leader position
and Follower position
"""

import numpy as np
import pyarrow as pa

from dora import Node

from common.position_control import in_range_position, adapt_range_goal


def main():
    node = Node("lcr_interpolate")

    follower_position = np.array([0, 0, 0, 0, 0, 0])

    for event in node:
        event_type = event["type"]

        if event_type == "INPUT":
            event_id = event["id"]

            if event_id == "leader_position":
                leader_position = event["value"][0]["positions"].values.to_numpy()
                leader_joints = event["value"][0]["joints"].values.to_numpy(zero_copy_only=False)

                goal_position = in_range_position(leader_position.copy())
                goal_position[5] = goal_position[5] * (700.0 / 450.0)

                """
                A communication issue with the follower can induces a +- 4096 offset in the position values.
                So we need to assure that the goal_position is in the range of the Follower.
                """
                goal_position = adapt_range_goal(goal_position, follower_position)

                goal_position_with_joints = {
                    "joints": leader_joints,
                    "positions": goal_position
                }

                node.send_output(
                    "goal_position",
                    pa.array([goal_position_with_joints]),
                    event["metadata"]
                )

            elif event_id == "follower_position":
                follower_position = event["value"][0]["positions"].values.to_numpy()
        elif event_type == "STOP":
            break
        elif event_type == "ERROR":
            print("[lcr_interpolate] error: ", event["error"])
            break


if __name__ == "__main__":
    main()
