"""Launch TurtleBot3 Gazebo, Nav2, and the RESILIENT-AMR planning stack."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    model = LaunchConfiguration("model")
    world_launch = LaunchConfiguration("world_launch")
    map_yaml = LaunchConfiguration("map")
    start_nav2 = LaunchConfiguration("start_nav2")
    enable_camera = LaunchConfiguration("enable_camera")
    memory_enabled = LaunchConfiguration("memory_enabled")
    experiment_condition = LaunchConfiguration("experiment_condition")
    experiment_log_path = LaunchConfiguration("experiment_log_path")
    use_sim_time = LaunchConfiguration("use_sim_time")
    params_file = LaunchConfiguration("params_file")
    memory_path = LaunchConfiguration("memory_path")
    use_rviz = LaunchConfiguration("use_rviz")
    default_params = PathJoinSubstitution([
        FindPackageShare("turtlebot3_navigation2"), "param", "humble", "waffle.yaml"])
    params = PathJoinSubstitution([FindPackageShare("resilient_amr_bringup"), "config", "nodes.yaml"])
    default_world_launch = PathJoinSubstitution([
        FindPackageShare("turtlebot3_gazebo"), "launch", "turtlebot3_world.launch.py"])
    default_map = PathJoinSubstitution([
        FindPackageShare("turtlebot3_navigation2"), "map", "map.yaml"])
    nav_launch = PathJoinSubstitution([
        FindPackageShare("nav2_bringup"), "launch", "bringup_launch.py"])
    rviz_config = PathJoinSubstitution([
        FindPackageShare("turtlebot3_navigation2"), "rviz", "tb3_navigation2.rviz"])

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(world_launch),
        launch_arguments={"use_sim_time": use_sim_time}.items())
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav_launch),
        condition=IfCondition(start_nav2),
        launch_arguments={"use_sim_time": use_sim_time, "map": map_yaml,
                          "params_file": params_file, "autostart": "true",
                          "use_localization": "true"}.items())

    nodes = [
        Node(package="resilient_amr_bringup", executable="change_memory", name="change_memory",
             parameters=[params, {"use_sim_time": ParameterValue(use_sim_time, value_type=bool),
                                  "memory_enabled": ParameterValue(memory_enabled, value_type=bool),
                                  "memory_path": memory_path}], output="screen"),
        Node(package="resilient_amr_bringup", executable="astar_planner", name="astar_planner",
             parameters=[params, {"use_sim_time": ParameterValue(use_sim_time, value_type=bool)}], output="screen"),
        Node(package="resilient_amr_bringup", executable="path_follower", name="path_follower",
             parameters=[params, {"use_sim_time": ParameterValue(use_sim_time, value_type=bool)}], output="screen"),
        Node(package="resilient_amr_bringup", executable="task_manager", name="task_manager",
             parameters=[params, {"use_sim_time": ParameterValue(use_sim_time, value_type=bool)}], output="screen"),
        Node(package="resilient_amr_bringup", executable="experiment_logger", name="experiment_logger",
             parameters=[params, {"use_sim_time": ParameterValue(use_sim_time, value_type=bool),
                                  "condition": experiment_condition, "log_path": experiment_log_path}], output="screen"),
        Node(package="resilient_amr_bringup", executable="aruco_detector", name="aruco_detector",
             condition=IfCondition(enable_camera), parameters=[params], output="screen"),
    ]
    return LaunchDescription([
        DeclareLaunchArgument("model", default_value="waffle", description="TurtleBot3 model"),
        DeclareLaunchArgument("world_launch", default_value=default_world_launch,
                              description="Gazebo world launch file"),
        DeclareLaunchArgument("map", default_value=default_map,
                              description="YAML map matching the selected Gazebo world"),
        DeclareLaunchArgument("start_nav2", default_value="true"),
        DeclareLaunchArgument("enable_camera", default_value="false",
                              description="Enable OpenCV ArUco detector when a camera topic is available"),
        DeclareLaunchArgument("memory_enabled", default_value="true",
                              description="Use persistent memory (false for A baseline)"),
        DeclareLaunchArgument("experiment_condition", default_value="B",
                              description="Experiment label written to JSONL logs"),
        DeclareLaunchArgument("experiment_log_path", default_value="~/.ros/resilient_amr/experiments/run.jsonl"),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("params_file", default_value=default_params),
        DeclareLaunchArgument("use_rviz", default_value="false"),
        DeclareLaunchArgument("memory_path", default_value="~/.ros/resilient_amr/environment_memory.json"),
        Node(package="rviz2", executable="rviz2", name="rviz2",
             arguments=["-d", rviz_config],
             parameters=[{"use_sim_time": ParameterValue(use_sim_time, value_type=bool)}],
             condition=IfCondition(use_rviz), output="screen"),
        SetEnvironmentVariable("TURTLEBOT3_MODEL", model),
        gazebo,
        nav2,
        *nodes,
    ])
