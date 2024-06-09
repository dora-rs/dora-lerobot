import argparse
import time

import cv2
import numpy as np
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
from reachy2_sdk import ReachySDK

parser = argparse.ArgumentParser()
parser.add_argument("--repo_id", type=str, required=True)
parser.add_argument("--episode", type=int, required=True)
args = parser.parse_args()

reachy = ReachySDK("localhost")

dataset = LeRobotDataset(args.repo_id)


from_index = dataset.episode_data_index["from"][args.episode]
to_index = dataset.episode_data_index["to"][args.episode]
actions = dataset.hf_dataset["action"][from_index:to_index]
states = dataset.hf_dataset["observation.state"][from_index:to_index]
images = dataset[from_index:to_index]["observation.images.cam_trunk"]
for i in range(len(actions)):

    image = images[i]
    image = cv2.cvtColor(
        (image.permute((1, 2, 0)).numpy() * 255).astype(np.uint8), cv2.COLOR_BGR2RGB
    )
    action = actions[i]
    cv2.imshow("image", image)
    cv2.waitKey(1)

    reachy.l_arm.shoulder.pitch.goal_position = np.rad2deg(action[0])
    reachy.l_arm.shoulder.roll.goal_position = np.rad2deg(action[1])
    reachy.l_arm.elbow.yaw.goal_position = np.rad2deg(action[2])
    reachy.l_arm.elbow.pitch.goal_position = np.rad2deg(action[3])
    reachy.l_arm.wrist.roll.goal_position = np.rad2deg(action[4])
    reachy.l_arm.wrist.pitch.goal_position = np.rad2deg(action[5])
    reachy.l_arm.wrist.yaw.goal_position = np.rad2deg(action[6])
    reachy.l_arm.gripper.set_opening(min(100, max(0, action[7] / 2.26 * 100)))

    reachy.r_arm.shoulder.pitch.goal_position = np.rad2deg(action[8])
    reachy.r_arm.shoulder.roll.goal_position = np.rad2deg(action[9])
    reachy.r_arm.elbow.yaw.goal_position = np.rad2deg(action[10])
    reachy.r_arm.elbow.pitch.goal_position = np.rad2deg(action[11])
    reachy.r_arm.wrist.roll.goal_position = np.rad2deg(action[12])
    reachy.r_arm.wrist.pitch.goal_position = np.rad2deg(action[13])
    reachy.r_arm.wrist.yaw.goal_position = np.rad2deg(action[14])
    reachy.r_arm.gripper.set_opening(min(100, max(0, action[15] / 2.26 * 100)))

    reachy.head.neck.roll.goal_position = np.rad2deg(action[19])
    reachy.head.neck.yaw.goal_position = np.rad2deg(action[20])
    reachy.head.neck.pitch.goal_position = np.rad2deg(action[21])

    time.sleep(1 / 30)
