"""Launch Nav2 with the packaged TurtleBot3 map, or an explicit map:= path."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    map_yaml = LaunchConfiguration("map")
    default_map = PathJoinSubstitution([
        FindPackageShare("turtlebot3_navigation2"), "map", "map.yaml"])
    nav_launch = PathJoinSubstitution([
        FindPackageShare("turtlebot3_navigation2"), "launch", "navigation2.launch.py"])
    return LaunchDescription([
        DeclareLaunchArgument("map", default_value=default_map),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(nav_launch),
                                 launch_arguments={"map": map_yaml,
                                                   "use_sim_time": LaunchConfiguration("use_sim_time")}.items()),
    ])
