"""Headless TurtleBot3 simulation in the matching open experiment arena."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    tb3 = get_package_share_directory("turtlebot3_gazebo")
    gazebo_ros = get_package_share_directory("gazebo_ros")
    root = os.path.dirname(__file__)
    world = os.path.join(root, "arena.world")
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(gazebo_ros, "launch", "gzserver.launch.py")),
            launch_arguments={"world": world}.items()),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(tb3, "launch", "robot_state_publisher.launch.py")),
            launch_arguments={"use_sim_time": LaunchConfiguration("use_sim_time", default="true")}.items()),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(tb3, "launch", "spawn_turtlebot3.launch.py")),
            launch_arguments={"x_pose": os.environ.get("RESILIENT_AMR_START_X", "-2.0"),
                              "y_pose": os.environ.get("RESILIENT_AMR_START_Y", "-2.0")}.items()),
    ])
