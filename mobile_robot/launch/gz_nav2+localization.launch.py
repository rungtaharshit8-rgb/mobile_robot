import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

from launch_ros.parameter_descriptions import ParameterValue
import xacro

def generate_launch_description():
    pkg = get_package_share_directory('mobile_robot')
    urdf_file = os.path.join(pkg, 'urdf', 'robot.urdf.xacro')

    # ── Read URDF ─────────────────────────────────────────────────────
    robot_description_xml = xacro.process_file(urdf_file).toxml()
    robot_description_param = ParameterValue(robot_description_xml, value_type=str)

    # ── Set Gazebo Resource Path ──────────────────────────────────────
    workspace_install = os.path.join(os.path.expanduser('~'), 'ros_ws', 'install')
    existing = os.environ.get('GZ_SIM_RESOURCE_PATH', '')

    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=existing + ':' + workspace_install if existing else workspace_install
    )

    world_file = os.path.join(pkg, 'worlds', 'multi_room.sdf')

    # ── 1. Gazebo Harmonic Simulator ──────────────────────────────────
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ]),
        launch_arguments={'gz_args': f'-r {world_file}', 'on_exit_shutdown': 'true'}.items()
    )

    # ── 2. robot_state_publisher ──────────────────────────────────────
    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description_param,
            'use_sim_time': True,
          }]
            )

    # ── 3. Spawn Robot in Gazebo ──────────────────────────────────────
    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'car', '-topic', 'robot_description', '-x', '1.0', '-y', '0.0', '-z', '0.10'],
        output='screen',
    )

    # ── 4. ROS-Gazebo Communication Bridge ────────────────────────────
    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
       arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/model/car/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/lidar@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/camera@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/camera/depth_image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            '/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            '/bumper_contact@ros_gz_interfaces/msg/Contacts[gz.msgs.Contacts',
        ],
        remappings=[
            ('/model/car/odometry', '/odom'),
        ],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    # ── 5. odom -> base_link TF ────────────────────────────────────────
    # NOTE: Nav2/amcl publishes map -> odom itself. This node must keep
    # publishing odom -> base_link (same as in SLAM mode) to complete the
    # TF chain: map -> odom -> base_link.
    odom_tf = Node(
        package='mobile_robot',
        executable='odom_tf_broadcaster.py',
        name='odom_tf_broadcaster',
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    # NOTE: slam_toolbox is intentionally NOT included here.
    # Running slam_toolbox at the same time as Nav2's map_server causes
    # both to publish conflicting data on /map -- map_server's static map
    # gets overwritten almost immediately by slam_toolbox's live map,
    # which is why the saved map flashed in RViz then disappeared.
    # For localization against a saved map, only map_server + amcl
    # (started separately via nav2_launch.py) should own /map.

    return LaunchDescription([
        gz_resource_path,
        gz_sim,
        rsp,
        spawn,
        gz_bridge,
        odom_tf,
    ])