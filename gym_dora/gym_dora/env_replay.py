import time

import cv2
import gymnasium as gym
import numpy as np
import pyarrow as pa
from dora import Node
from gymnasium import spaces
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

EPISODE = 19
REPO_ID = "cadene/reachy2_mobile_base"


class DoraEnv(gym.Env):
    metadata = {}

    def __init__(
        self,
        fps: int,
        actions: list[str],
        joints: list[str] | None = None,
        cameras: dict[str, tuple[int]] | None = None,
    ):
        self.fps = fps
        self.actions = actions
        self.joints = joints
        self.cameras = cameras
        self._node = Node()

        # Specify gym action and observation spaces

        observation_space = {}

        if self.joints:
            observation_space["agent_pos"] = spaces.Box(
                low=-1000.0,
                high=1000.0,
                shape=(len(self.joints),),
                dtype=np.float64,
            )

        if self.cameras:
            pixels_space = {}
            for camera, hwc_shape in cameras.items():
                # Assumes images are unsigned int8 in [0,255]
                pixels_space[camera] = spaces.Box(
                    low=0,
                    high=255,
                    # height x width x channels (e.g. 480 x 640 x 3)
                    shape=hwc_shape,
                    dtype=np.uint8,
                )
            observation_space["pixels"] = spaces.Dict(pixels_space)

        self.observation_space = spaces.Dict(observation_space)
        self.action_space = spaces.Box(
            low=-1, high=1, shape=(len(self.actions),), dtype=np.float32
        )

        # Initialize a new Dora node used to get events from the robot
        # that will be stored in `_observation` and `_terminated`
        self._observation = {"pixels": {}, "agent_pos": None}
        self._terminated = False
        self.dataset = LeRobotDataset(REPO_ID)
        self.from_index = self.dataset.episode_data_index["from"][EPISODE].item()
        self.to_index = self.dataset.episode_data_index["to"][EPISODE].item()

        self.index = 0

    def reset(self, seed: int | None = None):  # type: ignore
        del seed
        ## TODO(tao): Add reset event to the node
        # self._node.send_output("reset")
        self._terminated = False
        info = {}

        item = self.dataset[self.from_index + self.index]
        state = item["observation.state"]
        image = item["observation.images.cam_trunk"]
        image = image.permute((1, 2, 0)).numpy() * 255
        image = image.astype(np.uint8)

        if image.shape != (800, 1280, 3):  # , "image not in the right order"
            raise ValueError("image not in the right order")

        self._observation = {"pixels": {"cam_trunk": image}, "agent_pos": state.numpy()}

        return self._observation, info

    def step(self, action: np.ndarray):
        # if action is not None:
        # Send the action to the dataflow as action key.
        self._node.send_output("action", pa.array(action))

        # Send the action to the dataflow as action key.
        # Space observation so that they match the dataset
        ## Convert image from chw to hwc

        if self.from_index + self.index >= self.to_index:
            self._terminated = True
            return self._observation, 0, True, False, {}

        item = self.dataset[self.from_index + self.index]
        state = item["observation.state"]
        image = item["observation.images.cam_trunk"]
        image = image.permute((1, 2, 0)).numpy() * 255
        image = image.astype(np.uint8)

        if image.shape != (800, 1280, 3):  # , "image not in the right order"
            raise ValueError("image not in the right order")

        self._observation = {"pixels": {"cam_trunk": image}, "agent_pos": state.numpy()}
        # Reset the observation
        reward = 0
        terminated = truncated = self._terminated
        info = {}
        self.index += 1
        return self._observation, reward, terminated, truncated, info

    def render(self): ...

    def close(self):
        # Drop the node
        del self._node
        pass
        pass
