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

ros2 launch interbotix_xsarm_descriptions xsarm_description.launch.py robot_model:=wx200 use_joint_pub_gui:=true

# ros2 service call /vx250/torque_enable interbotix_xs_msgs/srv/TorqueEnable "{cmd_type: 'group', name: 'all', enable: false}"

# ros2 service call /vx250/torque_enable interbotix_xs_msgs/srv/TorqueEnable "{cmd_type: 'group', name: 'all', enable: true}"

# vim /root/interbotix_ws/src/interbotix_ros_toolboxes/interbotix_xs_toolbox/interbotix_xs_modules/interbotix_xs_modules/xs_robot/arm.py

# #  Change self.T_sb = mr.FKinSpace(self.robot_des.M, self.robot_des.Slist, self.joint_commands) to self.T_sb = None. This prevents the code from calculating FK at every step which delays teleoperation.

# colcon build

# # ros2 launch ...

# ros2 launch ~/interbotix_ws/src/interbotix_ros_manipulators/interbotix_ros_xsarms/interbotix_xsarm_control/launch/xsarm_control.launch.py robot_model:=wx250s  use_sim:=true


# # from interbotix_xs_modules.xs_robot.arm import InterbotixManipulatorXS
# # from interbotix_xs_msgs.msg import JointSingleCommand

