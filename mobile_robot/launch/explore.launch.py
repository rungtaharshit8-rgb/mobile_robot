import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """
    Frontier-based autonomous exploration.

    Requires, already running:
      - gz_launch.py            (Gazebo + bridge + slam_toolbox -> /map)
      - nav2_navigation_launch.py (controller/planner/behavior/bt_navigator,
                                    NOT nav2_launch.py -- no amcl while SLAM
                                    is live)

    explore_lite reads the global costmap (lidar-built, static_layer from
    slam_toolbox's /map) to pick frontier goals, and sends them to Nav2's
    navigate_to_pose action server. The depth camera doesn't factor into
    goal selection -- it only affects the LOCAL costmap's obstacle layer
    (see nav2_params.yaml), so it improves collision avoidance en route to
    each frontier without influencing which frontier gets picked.
    """
    pkg = get_package_share_directory('mobile_robot')
    params_file = os.path.join(pkg, 'config', 'explore_params.yaml')

    explore = Node(
        package='explore_lite',
        executable='explore',
        name='explore_node',
        output='screen',
        parameters=[params_file],
    )

    return LaunchDescription([explore])