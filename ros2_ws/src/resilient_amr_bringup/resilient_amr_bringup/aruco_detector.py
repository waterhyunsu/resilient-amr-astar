"""ArUco ID detection and one-shot AMCL initial-pose estimate from mapped tags."""

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image
from std_msgs.msg import Int32MultiArray
from tf2_ros import Buffer, TransformException, TransformListener


class ArucoDetector(Node):
    def __init__(self):
        super().__init__("aruco_detector")
        self.declare_parameter("image_topic", "/camera/image_raw")
        self.declare_parameter("camera_info_topic", "/camera/camera_info")
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("base_frame", "base_footprint")
        self.declare_parameter("dictionary", "DICT_4X4_50")
        self.declare_parameter("marker_size_m", 0.10)
        self.declare_parameter("reference_marker_ids", [])
        # Four values per ID: map x, y, z, and tag yaw in radians.
        self.declare_parameter("reference_marker_poses", [])
        self.bridge = CvBridge()
        self.camera_matrix = None
        self.distortion = None
        self.initialized = False
        aruco = cv2.aruco
        dictionary_id = getattr(aruco, self.get_parameter("dictionary").value)
        self.dictionary = aruco.getPredefinedDictionary(dictionary_id)
        if hasattr(aruco, "ArucoDetector"):
            self.detector = aruco.ArucoDetector(self.dictionary, aruco.DetectorParameters())
            self.detect = self.detector.detectMarkers
        else:
            parameters = aruco.DetectorParameters_create()
            self.detect = lambda image: aruco.detectMarkers(
                image, self.dictionary, parameters=parameters)
        self.ids_pub = self.create_publisher(Int32MultiArray, "/resilient_amr/aruco_ids", 10)
        self.initialpose_pub = self.create_publisher(
            PoseWithCovarianceStamped, "/initialpose", 10)
        self.create_subscription(CameraInfo, self.get_parameter("camera_info_topic").value,
                                 self.on_camera_info, 10)
        self.create_subscription(Image, self.get_parameter("image_topic").value,
                                 self.on_image, 10)
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def on_camera_info(self, message):
        self.camera_matrix = np.asarray(message.k, dtype=float).reshape(3, 3)
        self.distortion = np.asarray(message.d, dtype=float)

    def on_image(self, message):
        try:
            image = self.bridge.imgmsg_to_cv2(message, desired_encoding="mono8")
            corners, ids, _ = self.detect(image)
        except Exception as exc:
            self.get_logger().warning(f"Image/ArUco processing failed: {exc}")
            return
        detected = [] if ids is None else [int(marker_id) for marker_id in ids.flatten()]
        ids_message = Int32MultiArray()
        ids_message.data = detected
        self.ids_pub.publish(ids_message)
        if self.initialized or not detected or self.camera_matrix is None:
            return
        self.publish_initial_pose(message, corners, detected)

    def publish_initial_pose(self, image_message, corners, detected_ids):
        configured_ids = self.get_parameter("reference_marker_ids").value
        configured_poses = self.get_parameter("reference_marker_poses").value
        if len(configured_poses) != 4 * len(configured_ids):
            self.get_logger().error("reference_marker_poses must contain x,y,z,yaw for each ID")
            return
        pose_by_id = {int(marker_id): configured_poses[index * 4:index * 4 + 4]
                      for index, marker_id in enumerate(configured_ids)}
        known_index = next((i for i, marker_id in enumerate(detected_ids)
                            if marker_id in pose_by_id), None)
        if known_index is None:
            return
        try:
            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                [corners[known_index]], float(self.get_parameter("marker_size_m").value),
                self.camera_matrix, self.distortion)
            camera_r_marker, _ = cv2.Rodrigues(rvecs[0][0])
            camera_t_marker = np.asarray(tvecs[0][0], dtype=float)
            marker_id = detected_ids[known_index]
            map_x, map_y, map_z, marker_yaw = map(float, pose_by_id[marker_id])
            map_r_marker = self.rotation_z(marker_yaw)
            map_t_marker = np.asarray([map_x, map_y, map_z])
            camera_T_marker = self.transform(camera_r_marker, camera_t_marker)
            map_T_marker = self.transform(map_r_marker, map_t_marker)
            base_frame = self.get_parameter("base_frame").value
            camera_frame = image_message.header.frame_id
            base_T_camera_msg = self.tf_buffer.lookup_transform(
                base_frame, camera_frame, rclpy.time.Time())
            base_T_camera = self.from_transform(base_T_camera_msg.transform)
            map_T_base = map_T_marker @ np.linalg.inv(camera_T_marker) @ np.linalg.inv(base_T_camera)
        except (TransformException, cv2.error, ValueError, np.linalg.LinAlgError) as exc:
            self.get_logger().warning(f"Cannot initialize from ArUco marker yet: {exc}")
            return
        if self.initialpose_pub.get_subscription_count() == 0:
            return
        yaw = float(np.arctan2(map_T_base[1, 0], map_T_base[0, 0]))
        half_yaw = yaw / 2.0
        message = PoseWithCovarianceStamped()
        message.header.frame_id = self.get_parameter("map_frame").value
        message.header.stamp = self.get_clock().now().to_msg()
        message.pose.pose.position.x = float(map_T_base[0, 3])
        message.pose.pose.position.y = float(map_T_base[1, 3])
        message.pose.pose.position.z = float(map_T_base[2, 3])
        message.pose.pose.orientation.z = float(np.sin(half_yaw))
        message.pose.pose.orientation.w = float(np.cos(half_yaw))
        message.pose.covariance[0] = 0.04
        message.pose.covariance[7] = 0.04
        message.pose.covariance[35] = 0.09
        self.initialpose_pub.publish(message)
        self.initialized = True
        self.get_logger().info(f"Initialized AMCL from reference ArUco ID {marker_id}")

    @staticmethod
    def rotation_z(yaw):
        c, s = np.cos(yaw), np.sin(yaw)
        return np.asarray([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])

    @staticmethod
    def transform(rotation, translation):
        matrix = np.eye(4)
        matrix[:3, :3] = rotation
        matrix[:3, 3] = translation
        return matrix

    @classmethod
    def from_transform(cls, transform):
        q = transform.rotation
        rotation = np.asarray([
            [1 - 2 * (q.y*q.y + q.z*q.z), 2 * (q.x*q.y - q.z*q.w),
             2 * (q.x*q.z + q.y*q.w)],
            [2 * (q.x*q.y + q.z*q.w), 1 - 2 * (q.x*q.x + q.z*q.z),
             2 * (q.y*q.z - q.x*q.w)],
            [2 * (q.x*q.z - q.y*q.w), 2 * (q.y*q.z + q.x*q.w),
             1 - 2 * (q.x*q.x + q.y*q.y)],
        ])
        translation = np.asarray([transform.translation.x, transform.translation.y,
                                  transform.translation.z])
        return cls.transform(rotation, translation)


def main(args=None):
    rclpy.init(args=args)
    node = ArucoDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
