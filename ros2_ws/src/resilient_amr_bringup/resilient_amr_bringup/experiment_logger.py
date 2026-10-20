"""Append structured experiment events to JSON Lines for later A/B analysis."""

import json
import hashlib
import os
import time
import uuid
from pathlib import Path

import rclpy
from nav_msgs.msg import Path as NavPath
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray, String


class ExperimentLogger(Node):
    def __init__(self):
        super().__init__("experiment_logger")
        self.declare_parameter("log_path", "~/.ros/resilient_amr/experiments/run.jsonl")
        self.declare_parameter("run_id", str(uuid.uuid4()))
        self.declare_parameter("condition", "B")
        self.path = Path(os.path.expanduser(self.get_parameter("log_path").value))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path_hash = None
        self.memory = set()
        self.event("run_started", {"condition": self.get_parameter("condition").value})
        self.create_subscription(NavPath, "/resilient_amr/path", self.on_path, 10)
        self.create_subscription(Int32MultiArray, "/resilient_amr/remembered_cells", self.on_memory, 10)
        self.create_subscription(String, "/resilient_amr/task_status", self.on_task, 10)
        self.create_subscription(String, "/resilient_amr/navigation_status", self.on_navigation, 10)

    def event(self, kind, fields):
        record = {"wall_time_unix": time.time(), "run_id": self.get_parameter("run_id").value,
                  "condition": self.get_parameter("condition").value, "event": kind, **fields}
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")

    def on_path(self, msg):
        points = [(round(p.pose.position.x, 3), round(p.pose.position.y, 3)) for p in msg.poses]
        signature = hashlib.sha256(json.dumps(points).encode()).hexdigest()
        changed = signature != self.path_hash
        self.event("path_published", {"poses": len(points), "path_changed": changed,
                                      "path_signature": signature})
        self.path_hash = signature

    def on_memory(self, msg):
        updated = set(msg.data)
        added, removed = updated - self.memory, self.memory - updated
        if added or removed:
            self.event("memory_updated", {"cell_count": len(updated), "added_cells": sorted(added),
                                          "removed_cells": sorted(removed)})
        self.memory = updated

    def on_task(self, msg):
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            data = {"raw": msg.data}
        self.event("task_status", data)

    def on_navigation(self, msg):
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            data = {"raw": msg.data}
        self.event("navigation_status", data)


def main(args=None):
    rclpy.init(args=args)
    node = ExperimentLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.event("run_stopped", {})
        node.destroy_node()
        rclpy.shutdown()
