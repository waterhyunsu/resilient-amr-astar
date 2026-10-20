"""Small warehouse task FSM driven by shelf IDs and marker confirmations."""

import json

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray, String
from std_srvs.srv import Trigger


class TaskManager(Node):
    def __init__(self):
        super().__init__("task_manager")
        self.declare_parameter("shelf_ids", ["A", "B", "C"])
        self.declare_parameter("shelf_marker_ids", [1, 2, 3])
        self.declare_parameter("shelf_x", [1.0, 2.0, 3.0])
        self.declare_parameter("shelf_y", [0.0, 0.0, 0.0])
        self.declare_parameter("shelf_yaw", [0.0, 0.0, 0.0])
        self.declare_parameter("dropoff_marker_id", 4)
        self.declare_parameter("dropoff_x", 0.0)
        self.declare_parameter("dropoff_y", 0.0)
        self.declare_parameter("dropoff_yaw", 0.0)
        self.declare_parameter("marker_confirmations", 2)
        self.state = "IDLE"
        self.task = None
        self.marker_hits = 0
        self.goal_pub = self.create_publisher(PoseStamped, "/resilient_amr/goal", 10)
        self.status_pub = self.create_publisher(String, "/resilient_amr/task_status", 10)
        self.create_subscription(String, "/resilient_amr/submit_task", self.on_task, 10)
        self.create_subscription(String, "/resilient_amr/operator_confirm", self.on_operator, 10)
        self.create_subscription(Int32MultiArray, "/resilient_amr/aruco_ids", self.on_markers, 10)
        self.create_subscription(String, "/resilient_amr/navigation_status", self.on_navigation, 10)
        self.create_service(Trigger, "/resilient_amr/reset_task", self.reset_task)
        self.cancel_client = self.create_client(Trigger, "/resilient_amr/cancel_navigation")

    def on_task(self, msg):
        if self.state != "IDLE":
            self.publish_status("BUSY", "Finish or cancel the current task first")
            return
        try:
            self.task = json.loads(msg.data)
            if not isinstance(self.task, dict):
                raise ValueError("Task must be a JSON object")
            shelf_id = str(self.task["shelf_id"])
            ids = self.get_parameter("shelf_ids").value
            if shelf_id not in ids:
                raise ValueError(f"Unknown shelf_id {shelf_id}; configured: {ids}")
            self.task["shelf_index"] = ids.index(shelf_id)
            self.task["dropoff_id"] = str(self.task.get("dropoff_id", "D"))
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            self.publish_status("REJECTED", str(exc))
            return
        self.state = "TO_SHELF"
        self.marker_hits = 0
        self.send_shelf_goal()
        self.publish_status(self.state, "Moving to requested shelf")

    def send_shelf_goal(self):
        index = self.task["shelf_index"]
        self.send_goal(self.get_parameter("shelf_x").value[index],
                       self.get_parameter("shelf_y").value[index],
                       self.get_parameter("shelf_yaw").value[index])

    def send_dropoff_goal(self):
        self.send_goal(self.get_parameter("dropoff_x").value,
                       self.get_parameter("dropoff_y").value,
                       self.get_parameter("dropoff_yaw").value)

    def send_goal(self, x, y, yaw):
        from math import sin, cos
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.pose.position.x, goal.pose.position.y = float(x), float(y)
        goal.pose.orientation.z, goal.pose.orientation.w = sin(float(yaw) / 2), cos(float(yaw) / 2)
        self.goal_pub.publish(goal)

    def on_navigation(self, msg):
        try:
            status = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        if status.get("status") == "CANCELED":
            return
        if status.get("status") != "SUCCEEDED":
            if self.state not in ("IDLE", "COMPLETED"):
                self.state = "FAILED"
                self.publish_status(self.state, status.get("message", "Navigation failed"))
            return
        if self.state == "TO_SHELF":
            self.state = "VERIFY_SHELF"
            self.marker_hits = 0
            self.publish_status(self.state, "Waiting for expected shelf ArUco marker")
        elif self.state == "TO_DROPOFF":
            self.state = "VERIFY_DROPOFF"
            self.marker_hits = 0
            self.publish_status(self.state, "Waiting for delivery-point ArUco marker")

    def on_markers(self, msg):
        expected = None
        if self.state == "VERIFY_SHELF":
            expected = self.get_parameter("shelf_marker_ids").value[self.task["shelf_index"]]
        elif self.state == "VERIFY_DROPOFF":
            expected = self.get_parameter("dropoff_marker_id").value
        if expected is None:
            return
        if int(expected) in msg.data:
            self.marker_hits += 1
            if self.marker_hits >= self.get_parameter("marker_confirmations").value:
                if self.state == "VERIFY_SHELF":
                    self.state = "WAIT_LOAD"
                    self.publish_status(self.state, "Shelf verified; operator load and confirm")
                else:
                    self.state = "WAIT_UNLOAD"
                    self.publish_status(self.state, "Dropoff verified; operator unload and confirm")
        else:
            self.marker_hits = 0

    def on_operator(self, msg):
        command = msg.data.strip().lower()
        if self.state == "WAIT_LOAD" and command == "loaded":
            self.state = "TO_DROPOFF"
            self.send_dropoff_goal()
            self.publish_status(self.state, "Load confirmed; moving to dropoff")
        elif self.state == "WAIT_UNLOAD" and command == "unloaded":
            self.state = "COMPLETED"
            self.publish_status(self.state, "Delivery complete")
            self.task = None
            self.state = "IDLE"
        elif command == "cancel" and self.state != "IDLE":
            self.state = "FAILED"
            if self.cancel_client.service_is_ready():
                self.cancel_client.call_async(Trigger.Request())
            self.publish_status(self.state, "Cancellation requested")
        elif command == "reset" and self.state in ("FAILED", "COMPLETED"):
            self.task = None
            self.state = "IDLE"
            self.publish_status(self.state, "Task state reset")

    def reset_task(self, request, response):
        if self.state not in ("FAILED", "COMPLETED", "IDLE"):
            response.success = False
            response.message = f"Cannot reset while task is {self.state}; send cancel first"
            return response
        self.task = None
        self.state = "IDLE"
        self.publish_status(self.state, "Task state reset")
        response.success, response.message = True, "Task state reset"
        return response

    def publish_status(self, state, detail):
        msg = String()
        msg.data = json.dumps({"state": state, "detail": detail, "task": self.task})
        self.status_pub.publish(msg)
        self.get_logger().info(f"{state}: {detail}")


def main(args=None):
    rclpy.init(args=args)
    node = TaskManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
