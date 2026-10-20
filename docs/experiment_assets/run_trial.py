"""One repeatable headless Gazebo trial; emits machine-readable trial records."""

import argparse
import hashlib
import json
import math
import time
from pathlib import Path

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped, PoseStamped
from gazebo_msgs.srv import SpawnEntity, DeleteEntity
from rcl_interfaces.srv import SetParameters
from nav_msgs.msg import OccupancyGrid, Odometry, Path as NavPath
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from std_msgs.msg import Int32MultiArray
from std_msgs.msg import String
from std_srvs.srv import Empty, Trigger
from rclpy.parameter import Parameter


BOX = """<?xml version='1.0'?>
<sdf version='1.6'><model name='trial_obstacle'><static>true</static>
<link name='link'><collision name='collision'><geometry><box><size>0.45 0.45 1.0</size></box></geometry></collision>
<visual name='visual'><geometry><box><size>0.45 0.45 1.0</size></box></geometry>
<material><ambient>0.8 0.2 0.1 1</ambient><diffuse>0.8 0.2 0.1 1</diffuse></material></visual>
</link></model></sdf>"""


class Trial(Node):
    def __init__(self, args):
        super().__init__("repeat_trial_driver")
        self.args = args
        self.map_seen = False
        self.map_message = None
        self.memory_message_seen = False
        self.memory_cells = set()
        self.observed_cells = set()
        self.statuses = []
        self.path_count = 0
        self.path_changes = 0
        self.route_switches = 0
        self.last_path_signature = None
        self.last_route_key = None
        self.last_activity = time.monotonic()
        self.started_at = None
        self.distance = 0.0
        self.last_odom = None
        self.final_position = None
        map_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                             reliability=ReliabilityPolicy.RELIABLE)
        self.sub_map = self.create_subscription(OccupancyGrid, "/map", self.on_map, map_qos)
        self.sub_status = self.create_subscription(String, "/resilient_amr/navigation_status", self.on_status, 10)
        self.sub_path = self.create_subscription(NavPath, "/resilient_amr/path", self.on_path, 10)
        self.sub_odom = self.create_subscription(Odometry, "/odom", self.on_odom, 10)
        self.sub_memory = self.create_subscription(Int32MultiArray, "/resilient_amr/remembered_cells",
                                                   self.on_memory, map_qos)
        self.sub_observed = self.create_subscription(Int32MultiArray, "/resilient_amr/observed_obstacles",
                                                     self.on_observed, 10)
        self.pose_pub = self.create_publisher(PoseWithCovarianceStamped, "/initialpose", 10)
        self.goal_pub = self.create_publisher(PoseStamped, "/resilient_amr/goal", 10)
        self.spawn = self.create_client(SpawnEntity, "/spawn_entity")
        self.delete = self.create_client(DeleteEntity, "/delete_entity")
        self.reset = self.create_client(Empty, "/reset_world")
        self.clear_memory = self.create_client(Trigger, "/resilient_amr/clear_memory")
        self.change_memory_params = self.create_client(SetParameters, "/change_memory/set_parameters")
        self.logger_params = self.create_client(SetParameters, "/experiment_logger/set_parameters")

    def on_map(self, msg):
        self.map_seen = True
        self.map_message = msg

    def on_memory(self, msg):
        self.memory_message_seen = True
        self.memory_cells = set(msg.data)

    def on_observed(self, msg):
        self.observed_cells = set(msg.data)

    def local_memory_count(self, cells):
        if self.map_message is None:
            return None
        info = self.map_message.info
        ox, oy = info.origin.position.x, info.origin.position.y
        resolution = info.resolution
        cx = int(math.floor((self.args.obstacle_x - ox) / resolution))
        cy = int(math.floor((self.args.obstacle_y - oy) / resolution))
        radius = max(1, int(math.ceil(0.75 / resolution)))
        return sum(1 for index in cells
                   if abs(index % info.width - cx) <= radius
                   and abs(index // info.width - cy) <= radius)

    def on_status(self, msg):
        try:
            value = json.loads(msg.data).get("status")
        except Exception:
            value = msg.data
        self.statuses.append((time.time(), value))
        self.last_activity = time.monotonic()

    def on_path(self, msg):
        self.path_count += 1
        points = [(round(p.pose.position.x, 3), round(p.pose.position.y, 3)) for p in msg.poses]
        signature = hashlib.sha256(json.dumps(points).encode()).hexdigest()
        if signature != self.last_path_signature:
            self.path_changes += 1
        self.last_path_signature = signature
        route_key = self.route_key(points)
        # Full path hashes change as A* starts at a robot that has moved forward.
        # Track route stability separately using the side chosen near the obstacle.
        if route_key is not None:
            if self.last_route_key is not None and route_key != self.last_route_key:
                self.route_switches += 1
            self.last_route_key = route_key
        self.last_activity = time.monotonic()

    def route_key(self, points):
        if len(points) < 2:
            return None
        sx, sy = self.args.start_x, self.args.start_y
        gx, gy = self.args.goal_x, self.args.goal_y
        dx, dy = gx - sx, gy - sy
        length_sq = dx * dx + dy * dy
        if length_sq <= 1e-12:
            return None
        obstacle_u = ((self.args.obstacle_x - sx) * dx
                      + (self.args.obstacle_y - sy) * dy) / length_sq
        lateral = []
        for x, y in points:
            u = ((x - sx) * dx + (y - sy) * dy) / length_sq
            if abs(u - obstacle_u) > 0.10:
                continue
            cross_track = (dx * (y - sy) - dy * (x - sx)) / math.sqrt(length_sq)
            lateral.append(cross_track)
        if not lateral:
            return None
        largest = max(lateral, key=abs)
        if largest > 0.12:
            return "positive_detour"
        if largest < -0.12:
            return "negative_detour"
        return "direct"

    def on_odom(self, msg):
        p = msg.pose.pose.position
        position = (p.x, p.y)
        self.final_position = list(position)
        if self.started_at is not None and self.last_odom is not None:
            self.distance += math.hypot(position[0] - self.last_odom[0], position[1] - self.last_odom[1])
        self.last_odom = position

    def spin_until(self, predicate, timeout, what):
        end = time.monotonic() + timeout
        while rclpy.ok() and time.monotonic() < end:
            rclpy.spin_once(self, timeout_sec=0.1)
            if predicate():
                return
        raise TimeoutError(f"Timed out waiting for {what}")

    def call(self, client, request, label):
        self.spin_until(client.service_is_ready, 30, label + " service")
        future = client.call_async(request)
        self.spin_until(future.done, 30, label + " response")
        result = future.result()
        if hasattr(result, "success") and not result.success:
            detail = getattr(result, "status_message", getattr(result, "message", ""))
            raise RuntimeError(f"{label} failed: {detail}")
        return result

    def publish_initial_pose(self):
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = "map"
        # A zero stamp asks AMCL/TF to use the latest available transform,
        # avoiding the small future-time skew seen with Gazebo's simulation clock.
        msg.pose.pose.position.x = float(self.args.start_x)
        msg.pose.pose.position.y = float(self.args.start_y)
        msg.pose.pose.orientation.w = 1.0
        covariance = [0.0] * 36
        covariance[0], covariance[7], covariance[35] = 0.05, 0.05, 0.03
        msg.pose.covariance = covariance
        for _ in range(6):
            self.pose_pub.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.5)

    def run(self):
        self.spin_until(lambda: self.map_seen and self.memory_message_seen
                        and self.goal_pub.get_subscription_count() >= 2
                        and self.status_pub_count() >= 1, 120, "map and experiment graph")
        # Remove leftovers from an interrupted run; then reset robot to its world spawn pose.
        try:
            self.call(self.delete, DeleteEntity.Request(name="trial_obstacle"), "delete leftover obstacle")
        except Exception:
            pass
        if self.args.reset_world:
            self.call(self.reset, Empty.Request(), "reset world")
        memory_request = SetParameters.Request()
        memory_request.parameters = [Parameter(name="memory_enabled", value=self.args.memory_enabled).to_parameter_msg()]
        self.call(self.change_memory_params, memory_request, "set memory mode")
        logger_request = SetParameters.Request()
        logger_request.parameters = [Parameter(name="condition", value=self.args.condition).to_parameter_msg()]
        self.call(self.logger_params, logger_request, "set logger condition")
        if not self.args.preserve_memory:
            clear_response = self.call(self.clear_memory, Trigger.Request(), "clear trial memory")
            if not clear_response.success:
                raise RuntimeError("clear trial memory failed: " + clear_response.message)
        if self.args.obstacle:
            request = SpawnEntity.Request()
            request.name = "trial_obstacle"
            request.xml = BOX
            request.initial_pose.position.x = float(self.args.obstacle_x)
            request.initial_pose.position.y = float(self.args.obstacle_y)
            request.initial_pose.position.z = 0.5
            self.call(self.spawn, request, "spawn obstacle")
        delay_end = time.monotonic() + self.args.appearance_delay
        while rclpy.ok() and time.monotonic() < delay_end:
            rclpy.spin_once(self, timeout_sec=0.1)
        self.publish_initial_pose()
        # Give AMCL time to publish map->odom->base_footprint before requesting a route.
        time.sleep(2.0)
        self.statuses.clear()
        self.path_count = 0
        self.path_changes = 0
        self.route_switches = 0
        self.last_path_signature = None
        self.last_route_key = None
        self.distance = 0.0
        self.last_odom = None
        self.started_at = time.monotonic()
        memory_start_count = len(self.memory_cells)
        local_memory_start_count = self.local_memory_count(self.memory_cells)
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.pose.position.x = float(self.args.goal_x)
        goal.pose.position.y = float(self.args.goal_y)
        goal.pose.orientation.w = 1.0
        self.goal_pub.publish(goal)
        if self.args.transient_seconds > 0 and self.args.obstacle:
            time.sleep(self.args.transient_seconds)
            self.call(self.delete, DeleteEntity.Request(name="trial_obstacle"), "remove transient obstacle")
        # FollowPath failures may be followed by a new A* path and another attempt.
        # Only SUCCESS is immediately final; classify failure after a quiet interval.
        deadline = time.monotonic() + self.args.timeout
        terminal = "UNKNOWN"
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            recent = [s for _, s in self.statuses]
            if "SUCCEEDED" in recent:
                terminal = "SUCCEEDED"
                break
            if "FAILED" in recent and time.monotonic() - self.last_activity >= self.args.failure_quiet_sec:
                terminal = "FAILED"
                break
        record = {"trial_id": self.args.trial_id, "phase": self.args.phase,
                  "condition": self.args.condition, "seed": self.args.seed,
                  "progress_checker_required_radius_m": self.args.progress_radius,
                  "goal_yaw_tolerance_rad": self.args.yaw_tolerance,
                  "status": terminal, "duration_sec": round(time.monotonic() - self.started_at, 3),
                  "odom_distance_m": round(self.distance, 3),
                  "path_messages": self.path_count, "path_changes": self.path_changes,
                  "replans_after_initial_path": max(0, self.path_count - 1),
                  "route_switches": self.route_switches,
                  "canceled_followpath_count": sum(status == "CANCELED" for _, status in self.statuses),
                  "final_position": self.final_position, "start": [self.args.start_x, self.args.start_y],
                  "goal": [self.args.goal_x, self.args.goal_y],
                  "obstacle": ([self.args.obstacle_x, self.args.obstacle_y] if self.args.obstacle else None),
                  "transient_seconds": self.args.transient_seconds,
                  "appearance_delay_sec": self.args.appearance_delay,
                  "memory_restored": (self.memory_message_seen and memory_start_count > 0)
                  if self.args.preserve_memory else None,
                  "memory_cells_at_start": memory_start_count,
                  "memory_cells_at_end": len(self.memory_cells),
                  "memory_cells_near_obstacle_at_start": local_memory_start_count,
                  "memory_cells_near_obstacle_at_end": self.local_memory_count(self.memory_cells),
                  "telemetry_statuses": [s for _, s in self.statuses]}
        with Path(self.args.output).open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record) + "\n")
        print(json.dumps(record), flush=True)

    def status_pub_count(self):
        return self.get_publishers_info_by_topic("/resilient_amr/navigation_status").__len__()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trial-id", required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--condition", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--obstacle", action="store_true")
    parser.add_argument("--transient-seconds", type=float, default=0)
    parser.add_argument("--appearance-delay", type=float, default=0)
    parser.add_argument("--obstacle-x", type=float, default=0)
    parser.add_argument("--obstacle-y", type=float, default=0)
    parser.add_argument("--start-x", type=float, default=-2)
    parser.add_argument("--start-y", type=float, default=-2)
    parser.add_argument("--goal-x", type=float, default=2)
    parser.add_argument("--goal-y", type=float, default=2)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--failure-quiet-sec", type=float, default=25)
    parser.add_argument("--progress-radius", type=float, default=0.5)
    parser.add_argument("--yaw-tolerance", type=float, default=0.25)
    parser.add_argument("--memory-enabled", action="store_true")
    parser.add_argument("--preserve-memory", action="store_true",
                        help="Do not clear remembered cells loaded at launch")
    parser.add_argument("--reset-world", action="store_true",
                        help="Reset Gazebo world; use only when starting from a verified fresh stack")
    args = parser.parse_args()
    rclpy.init()
    node = Trial(args)
    try:
        node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
