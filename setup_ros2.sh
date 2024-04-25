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

ros2 launch interbotix_xsarm_descriptions xsarm_description.launch.py robot_model:=wx250 robot_name:=ttyDXL_master_left use_joint_pub_gui:=true &

# ros2 service call /aloha_vx250/torque_enable interbotix_xs_msgs/srv/TorqueEnable "{cmd_type: 'group', name: 'all', enable: false}"

# ros2 service call /aloha_wx250s/torque_enable interbotix_xs_msgs/srv/TorqueEnable "{cmd_type: 'group', name: 'all', enable: true}"

# vim /root/interbotix_ws/src/interbotix_ros_toolboxes/interbotix_xs_toolbox/interbotix_xs_modules/interbotix_xs_modules/xs_robot/arm.py

# #  Change self.T_sb = mr.FKinSpace(self.robot_des.M, self.robot_des.Slist, self.joint_commands) to self.T_sb = None. This prevents the code from calculating FK at every step which delays teleoperation.

# colcon build

# # ros2 launch ...

ros2 launch ~/interbotix_ws/src/interbotix_ros_manipulators/interbotix_ros_xsarms/interbotix_xsarm_control/launch/xsarm_control.launch.py robot_name:=robot_model_master robot_model:=aloha_wx250s &
ros2 launch ~/interbotix_ws/src/interbotix_ros_manipulators/interbotix_ros_xsarms/interbotix_xsarm_control/launch/xsarm_control.launch.py robot_name:=robot_model_puppet robot_model:=aloha_vx300s & # use_sim:=true


ros2 launch ~/interbotix_ws/src/interbotix_ros_manipulators/interbotix_ros_xsarms/interbotix_xsarm_control/launch/xsarm_control.launch.py robot_name:=robot_model_puppet robot_model:=aloha_vx300s use_sim:=true &

## Dearm Master and arm puppet
ros2 service call /robot_model_master/torque_enable interbotix_xs_msgs/srv/TorqueEnable "{cmd_type: 'group', name: 'all', enable: false}"

ros2 service call /robot_model_puppet/torque_enable interbotix_xs_msgs/srv/TorqueEnable "{cmd_type: 'group', name: 'all', enable: true}"

## Setting PID
# ros2 service call /robot_model_puppet/set_motor_pid_gains interbotix_xs_msgs/srv/MotorGains "{cmd_type: 'group', name: 'all', kp_pos: 800, ki_pos: 0}"

## Setting OperatingMode
ros2 service call /robot_model_puppet/set_operating_modes interbotix_xs_msgs/srv/OperatingModes "{cmd_type: 'group', name: 'all', mode: 'position'}"


# # from interbotix_xs_modules.xs_robot.arm import InterbotixManipulatorXS
# # from interbotix_xs_msgs.msg import JointSingleCommand
