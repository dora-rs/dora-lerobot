import gymnasium as gym
import numpy as np
import pyarrow as pa
from dora import Node
from gymnasium import spaces
import time


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
        self._node = Node()
        self._observation = {"pixels": {}, "agent_pos": None}
        self._terminated = False
        self._step_time = time.time()

    def _get_obs(self):
        obs_initial_time = time.time()
        while time.time() - obs_initial_time < 1 / self.fps:
            event = self._node.next(timeout=0.001)

            ## If event is None, the node event stream is closed and we should terminate the env
            if event is None:
                self._terminated = True
                print("Node event stream closed.")
                raise ConnectionError("Dora Node event stream closed.")

            if event["type"] == "INPUT":
                # Map Image input into pixels key within Aloha environment
                if "cam" in event["id"]:
                    camera = event["id"]
                    hwc_shape = self.cameras[camera]
                    self._observation["pixels"][event["id"]] = (
                        event["value"].to_numpy().reshape(hwc_shape)
                    )
                else:
                    # Map other inputs into the observation dictionary using the event id as key
                    self._observation[event["id"]] = event["value"].to_numpy()

            # If the event is a timeout error break the update loop.
            elif event["type"] == "ERROR":
                break

    def reset(self, seed: int | None = None):
        del seed
        ## TODO(tao): Add reset event to the node
        # self._node.send_output("reset")
        self._get_obs()
        self._terminated = False
        info = {}
        return self._observation, info

    def step(self, action: np.ndarray):
        # Send the action to the dataflow as action key.
        time.sleep(max(0, 1 / self.fps - (time.time() - self._step_time)))
        self._node.send_output("action", pa.array(action))

        # Space observation so that they match the dataset
        self._step_time = time.time()

        # Reset the observation
        self._get_obs()
        reward = 0
        terminated = truncated = self._terminated
        info = {}
        return self._observation, reward, terminated, truncated, info

    def render(self): ...

    def close(self):
        # Drop the node
        del self._node
