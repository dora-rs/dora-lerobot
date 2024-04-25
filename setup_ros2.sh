# setup ros2


## Within the docker container

## Source: https://docs.trossenrobotics.com/interbotix_xsarms_docs/ros_interface/ros2/software_setup.html

sudo apt update

sudo apt install curl vim git -y

curl 'https://raw.githubusercontent.com/Interbotix/interbotix_ros_manipulators/humble/interbotix_ros_xsarms/install/amd64/xsarm_amd64_install.sh' > xsarm_amd64_install.sh

source /opt/ros/$ROS_DISTRO/setup.bash

chmod +x xsarm_amd64_install.sh

./xsarm_amd64_install.sh -d humble -n

## Andswer

## Follow CLI interface withotu matlab

## Check

source /opt/ros/$ROS_DISTRO/setup.bash

source ~/interbotix_ws/install/setup.bash

ros2 pkg list | grep interbotix


## Simulator 

# ros2 launch interbotix_xsarm_descriptions xsarm_description.launch.py robot_model:=wx250 robot_name:=ttyDXL_master_left use_joint_pub_gui:=true &


ros2 launch ~/interbotix_ws/src/interbotix_ros_manipulators/interbotix_ros_xsarms/interbotix_xsarm_control/launch/xsarm_control.launch.py robot_name:=robot_model_master robot_model:=aloha_wx250s  mode_configs:=/dora-aloha/config/master_modes_right.yaml  &
ros2 launch ~/interbotix_ws/src/interbotix_ros_manipulators/interbotix_ros_xsarms/interbotix_xsarm_control/launch/xsarm_control.launch.py robot_name:=robot_model_puppet robot_model:=aloha_vx300s use_gripper:=true mode_configs:=/dora-aloha/config/puppet_modes_right.yaml  &

## Dearm Master and arm puppet
# ros2 service call /robot_model_master/torque_enable interbotix_xs_msgs/srv/TorqueEnable "{cmd_type: 'group', name: 'all', enable: false}"

# ros2 service call /robot_model_puppet/torque_enable interbotix_xs_msgs/srv/TorqueEnable "{cmd_type: 'group', name: 'all', enable: true}"

## Setting OperatingMode
# ros2 service call /robot_model_puppet/set_operating_modes interbotix_xs_msgs/srv/OperatingModes "{cmd_type: 'group', name: 'all', mode: 'position'}"

