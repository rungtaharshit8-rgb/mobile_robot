# Mobile Robot

A ROS 2 Jazzy + Gazebo Harmonic package for a differential-drive robot, supporting two workflows:

1. **SLAM mapping** — drive the robot around and build a map with `slam_toolbox`.
2. **Nav2 localization** — load a saved static map and localize/navigate against it with AMCL + Nav2.

The two workflows live in separate launch files so their `/map` publishers never collide.

---

## Prerequisites

- ROS 2 Jazzy
- Gazebo Harmonic
- `ros_gz_bridge`
- `slam_toolbox` (online async mode)
- `nav2_bringup`, `nav2_map_server`, `nav2_amcl`

## Workspace layout

```
~/ros_ws/
└── src/
    └── mobile_robot/
        ├── launch/
        │   ├── gz_slam_mapping.launch.py       
        │   ├── gz_nav2_localization.launch.py   
        │   └── nav2_launch.py                  
        ├── maps/
        │   ├── multi_room_map.pgm
        │   └── multi_room_map.yaml
        ├── params/
        │   └── nav2_params.yaml
        ├── scripts/
        │   └── odom_tf_broadcaster.py
        ├── CMakeLists.txt
        └── package.xml
```

## Build

```bash
cd ~/ros_ws
colcon build --packages-select car
source install/setup.bash
```

---

## Workflow 1: SLAM Mapping

Brings up Gazebo, the robot, the ROS–Gazebo bridge, and `slam_toolbox` in online async mode to build a map from `/lidar` scans.

```bash
ros2 launch mobile_robot gz_slam.launch.py
```

Drive the robot around (teleop or a script) until the map looks complete, 
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard 
```

then save it:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/ros_ws/src/mobile_robot/maps/multi_room_map
```

**Notes**

- `slam_toolbox`'s default map update rate is 0.1 Hz (every 10s). If you're pairing this with frontier exploration, override it with `map_update_interval: 2.0` in the SLAM params, otherwise the map updates slower than the exploration goal-picking cycle.
- `slam_toolbox` requires explicit configure/activate lifecycle transitions and won't subscribe to `/lidar` until activated.
- Do **not** run `map_server` at the same time as `slam_toolbox` — both publishing `/map` causes the map to flash and disappear in RViz.

---

## Workflow 2: Nav2 Localization (static map)

Brings up Gazebo, the robot, the bridge, and `odom_tf_broadcaster` — **no** `slam_toolbox` — then loads the saved map and runs AMCL + Nav2 against it.

```bash
# Terminal 1: simulation
ros2 launch mobile_robot gz_nav2+localization.launch.py

# Terminal 2: localization + navigation stack
ros2 launch mobile_robot nav2.launch.py map:=/home/<you>/ros_ws/src/mobile_robot/maps/multi_room_map.yaml
```

In RViz:
1. Set **Fixed Frame** to `map`.
2. Use **2D Pose Estimate** to give AMCL an initial guess (or rely on `set_initial_pose` in params — see below).
3. Confirm localization with:
   ```bash
   ros2 run tf2_ros tf2_echo map odom
   ```
   A steady, non-zero `map → odom` transform means AMCL is working.
4. Send goals via **2D Nav Goal** or the Nav2 action API.

**Key `nav2_params.yaml` settings**

- `set_initial_pose: true`
- `scan_topic: /lidar`
- `use_sim_time: true` (set consistently across every node)

> AMCL parameters go in `nav2_params.yaml`, **not** the map's `.yaml` file — that file only describes map metadata (resolution, origin, image path).

---

## Roadmap

- [ ] Confirm end-to-end Nav2 goal-sending against the static map
- [ ] Resolve `explore_lite` frontier exploration (twitching without translating; near-zero-distance goals after tuning `min_frontier_size`, `footprint_clearing_enabled`, `gain_scale`/`potential_scale`)
