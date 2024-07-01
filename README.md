# Dora-LeRobot

Dora-LeRobot is a 100% Dora pipeline for manipulating robots, cameras and all possible hardware compatible with LeRobot.

## About Dora

Dora is a framework that lets you build applications by connecting components (nodes) together. It is based on the
concept of a graph where nodes are connected by edges. Each node can have inputs and outputs that are connected to other
nodes. The nodes can be written in any language and can be run on any platform. The communication between nodes is done
via a shared memory space.

Building a robotic application can be summed up as bringing together hardware, algorithms, and AI models, and make them
communicate with each others. At dora-rs, we try to:

- make integration of hardware and software easy by supporting Python, C, C++, and also ROS2.
- make communication low latency by using zero-copy Arrow messages.

You can see more about Dora in the [Dora repository](https://github.com/dora-rs/dora).

## About LeRobot

🤗 LeRobot aims to provide models, datasets, and tools for real-world robotics in PyTorch. The goal is to lower the
barrier to entry to robotics so that everyone can contribute and benefit from sharing datasets and pretrained models.

🤗 LeRobot contains state-of-the-art approaches that have been shown to transfer to the real-world with a focus on
imitation learning and reinforcement learning.

🤗 LeRobot already provides a set of pretrained models, datasets with human collected demonstrations, and simulation
environments to get started without assembling a robot. In the coming weeks, the plan is to add more and more support
for real-world robotics on the most affordable and capable robots out there.

🤗 LeRobot hosts pretrained models and datasets on this Hugging Face community page: huggingface.co/lerobot

You can see more about LeRobot in the [LeRobot repository](https://github.com/huggingface/lerobot/)

## Robots that we support

Inside the `robots` folder, you will find all the robots that we support. Each robot has its own README file that
contains all the information about the robot, how to assemble it, how to use it, and how to integrate it with Dora.

The philosophy of those robots support, is that we want to provide really agnostic nodes inside the `node_hub` folder
that can be used with any robot. This way, you can use the same nodes with different robots, and you can also use the
same robot with different nodes.

Of course, you can also create your own support for your own robot, and we will be happy to help you with that.

Here are the robots that we support: [robots/README.md](robots/README.md)

## License

This library is licensed under the [Apache License 2.0](./LICENSE).
