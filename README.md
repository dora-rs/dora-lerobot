# `dora-rs` powered ALOHA

## Getting started

```bash
docker run  --name ros2-aloha --network=host -e DISPLAY=${DISPLAY} -v $(pwd):/dora-aloha -it osrf/ros:humble-desktop


## In the container

# Run setup_ros2.sh
./dora-aloha/setup_ros2.sh

# After the setup. You can always go back in this container with:

docker start ros2-aloha

docker exec -it ros2-aloha /bin/bash

ros2 launch interbotix_xsarm_descriptions xsarm_description.launch.py robot_model:=wx200 use_joint_pub_gui:=true
```

## To run dora

```bash

## Setup
git clone https://github.com/haixuanTao/ament_prefix_path.git $HOME/ros2-ament-prefix-path
export AMENT_PREFIX_PATH=$HOME/ros2-ament-prefix-path # <- This holds ros2 message deserialization


## Start

dora up
dora start dataflow.yml --attach

```
