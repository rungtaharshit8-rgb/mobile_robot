#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped


class OdomTFBroadcaster(Node):
    """Subscribe to odometry and broadcast as TF with fixed frame names."""

    def __init__(self): 
        super().__init__('odom_tf_broadcaster')

        # Create TF broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)    

        # Subscribe to odometry topic
        self.subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10)

        self.get_logger().info('Odometry TF broadcaster initialized')

    def odom_callback(self, msg: Odometry) -> None:
        """
        Process odometry messages and broadcast as TF.

        Args:
            msg: Odometry message from Gazebo/simulator
        """
        # Create transform message
        transform = TransformStamped()

        # Set header with timestamp and parent frame
        # FIXED: use the odometry message's own stamp (when the sample was
        # actually taken in sim) rather than self.get_clock().now() (when
        # this callback happens to run). Under use_sim_time these can drift
        # apart, and slam_toolbox is sensitive enough to that drift that it
        # smears the map.
        transform.header.stamp = msg.header.stamp

        # FIXED: hardcode unprefixed frame names instead of copying
        # msg.header.frame_id / msg.child_frame_id, which still contain
        # Gazebo's "car/" prefix baked into the message content.
        transform.header.frame_id = 'odom'
        transform.child_frame_id = 'base_link'

        # Copy position from odometry pose (values are correct regardless
        # of the prefix used in the message's own frame_id fields)
        transform.transform.translation.x = msg.pose.pose.position.x
        transform.transform.translation.y = msg.pose.pose.position.y
        transform.transform.translation.z = msg.pose.pose.position.z

        # Copy orientation from odometry pose
        transform.transform.rotation = msg.pose.pose.orientation

        # Broadcast the transform
        self.tf_broadcaster.sendTransform(transform)


def main(args=None):
    """Initialize ROS and run the broadcaster node."""
    rclpy.init(args=args)
    broadcaster = OdomTFBroadcaster()

    try:
        rclpy.spin(broadcaster)
    except KeyboardInterrupt:
        pass
    finally:
        broadcaster.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()