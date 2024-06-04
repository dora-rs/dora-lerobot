import gymnasium as gym
import numpy as np
import pyarrow as pa
from dora import Node
from gymnasium import spaces
import time
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
import cv2


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
        episode = 1
        dataset = LeRobotDataset("cadene/reachy2_teleop_remi")
        from_index = dataset.episode_data_index["from"][episode]
        to_index = dataset.episode_data_index["to"][episode]
        self.actions = dataset.hf_dataset["action"][from_index:to_index]
        self.states = dataset.hf_dataset["observation.state"][from_index:to_index]

        self.images = dataset[from_index:to_index]["observation.images.cam_trunk"]
        self.index = 0

    def reset(self, seed: int | None = None):
        del seed
        ## TODO(tao): Add reset event to the node
        # self._node.send_output("reset")
        self._terminated = False
        info = {}
        frame_chw = self.images[self.index]
        frame_hwc = frame_chw.permute((1, 2, 0)).numpy() * 255
        assert frame_hwc.shape == (800, 1280, 3), "image not in the right order"
        frame_hwc = frame_hwc.astype(np.uint8)
        # image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        pos = self.states[self.index].numpy()
        self._observation = {"pixels": {"cam_trunk": frame_hwc}, "agent_pos": pos}

        return self._observation, info

    def step(self, action: np.ndarray):
        self._node.send_output("action", pa.array(action))

        # Send the action to the dataflow as action key.
        # Space observation so that they match the dataset
        ## Convert image from chw to hwc

        # cv2.imwrite("test.jpg", (images.permute((1, 2, 0)).numpy() * 255).astype(np.uint8))
        if self.index >= len(self.images):
            self._terminated = True
            return self._observation, 0, True, False, {}
        image = self.images[self.index]
        image = image.permute((1, 2, 0)).numpy() * 255
        image = image.astype(np.uint8)
        # image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        pos = self.states[self.index].numpy()
        self._observation = {"pixels": {"cam_trunk": image}, "agent_pos": pos}
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
