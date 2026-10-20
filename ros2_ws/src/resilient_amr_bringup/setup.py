from glob import glob
from setuptools import setup

package_name = "resilient_amr_bringup"

setup(
    name=package_name,
    version="0.2.0",
    packages=[package_name, "resilient_amr"],
    package_dir={"resilient_amr": "../../../src/resilient_amr"},
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
        ("share/" + package_name + "/models", glob("models/*.sdf")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="RESILIENT-AMR project",
    maintainer_email="maintainer@example.invalid",
    description="TurtleBot3 ROS 2 simulation and persistent memory planning.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "change_memory = resilient_amr_bringup.change_memory:main",
            "astar_planner = resilient_amr_bringup.astar_planner:main",
            "path_follower = resilient_amr_bringup.path_follower:main",
            "task_manager = resilient_amr_bringup.task_manager:main",
            "aruco_detector = resilient_amr_bringup.aruco_detector:main",
            "experiment_logger = resilient_amr_bringup.experiment_logger:main",
        ],
    },
)
