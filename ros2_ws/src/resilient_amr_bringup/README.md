# Gazebo 시뮬레이션 실행

대상 실행 환경은 ROS 2 Humble과 TurtleBot3 Gazebo/Nav2가 설치된 Ubuntu 22.04 WSL2입니다. Gazebo Classic용 TurtleBot3 `turtlebot3_world`와 패키지의 기본 world/map을 사용하며 모델은 `waffle`입니다. 이 프로젝트는 headless 통합 실행으로 검증했습니다. GUI RViz/Gazebo 렌더링은 검증 범위에 포함되지 않습니다.

반복 시험 설계, 결과, 실패와 신뢰구간은 [검증 보고서](../../../docs/VALIDATION_REPORT_2026-10-20.md), 반복 규칙은 [실험 프로토콜](../../../docs/EXPERIMENT_PROTOCOL.md)를 참고하세요. ROS 통신과 자체 A* FollowPath 주행, 기억 저장·재시작 복원·제거를 확인했지만 지속 장애물 조건의 재계획 감소 가설은 통계적으로 입증되지 않았고 일부 주행은 Nav2 progress 검사에서 중단됐습니다.

## 빌드

저장소를 Ubuntu 22.04 WSL2에서 clone하거나 접근한 뒤:

```bash
cd resilient-amr-astar/ros2_ws
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=waffle
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
```

## 전체 시뮬레이션 launch

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
export TURTLEBOT3_MODEL=waffle
ros2 launch resilient_amr_bringup sim.launch.py
```

다른 모델, world, map을 지정할 수 있습니다.

```bash
ros2 launch resilient_amr_bringup sim.launch.py \
  model:=burger \
  world_launch:=/절대경로/your_world.launch.py \
  map:=/절대경로/your_map.yaml
```

실행 중 확인할 항목:

```bash
ros2 topic list
ros2 topic echo /map --once
ros2 topic echo /scan --once
ros2 run tf2_ros tf2_echo map base_footprint
ros2 action list | grep follow_path
```

## A* 목적지 지정

초기 위치 추정과 Nav2가 준비된 뒤 목표를 `map` 프레임 pose로 보냅니다. 목표 위치는 현재 map의 자유 셀 안에 지정해야 합니다.

```bash
ros2 topic pub --once /resilient_amr/goal geometry_msgs/msg/PoseStamped \
  "{header: {frame_id: map}, pose: {position: {x: 1.0, y: 0.0, z: 0.0}, orientation: {z: 0.0, w: 1.0}}}"
```

`astar_planner`가 `/resilient_amr/path`를 만들고 `path_follower`가 Nav2 `FollowPath` action으로 전달합니다. A* 자체 경로를 확인하려면 다음을 사용합니다.

```bash
ros2 topic echo /resilient_amr/path
```

## ArUco 기반 선반-배송 임무

카메라 토픽이 있는 world/robot 모델에서 detector를 켭니다. detector는 마커 ID를 내보내고, 설정한 기준 마커 pose와 CameraInfo 및 TF의 camera-to-base 변환을 이용해 AMCL의 `/initialpose`를 한 번 초기화합니다. 기본 `reference_marker_ids`/ `reference_marker_poses`는 비어 있으므로 실제 마커 ID와 map 좌표를 `config/nodes.yaml`에 등록해야 자동 초기화가 작동합니다. 마커 pose 배열은 ID 순서대로 `x, y, z, yaw` 네 값씩 지정합니다.

```bash
ros2 launch resilient_amr_bringup sim.launch.py enable_camera:=true
ros2 topic pub --once /resilient_amr/submit_task std_msgs/msg/String \
  "{data: '{\"shelf_id\":\"B\",\"dropoff_id\":\"D\"}'}"
```

작업 상태를 확인하고, 선반에서 적재를 마친 뒤 `loaded`, 배송 지점에서 하역을 마친 뒤 `unloaded`를 보냅니다.

```bash
ros2 topic echo /resilient_amr/task_status
ros2 topic pub --once /resilient_amr/operator_confirm std_msgs/msg/String "{data: loaded}"
ros2 topic pub --once /resilient_amr/operator_confirm std_msgs/msg/String "{data: unloaded}"
```

선반 접근 위치와 배송 위치는 `config/nodes.yaml`의 `shelf_x/y/yaw`, `dropoff_x/y/yaw`를 실제 map에 맞게 수정해야 합니다. 마커 ID 목록도 실제 출력물과 맞춰야 합니다.

## 기억 저장/초기화 및 재시작 확인

메모리는 기준 지도 파일을 수정하지 않고 `~/.ros/resilient_amr/environment_memory.json`에 저장합니다.

```bash
ros2 service call /resilient_amr/save_memory std_srvs/srv/Trigger "{}"
```

시뮬레이션 중 지도상 자유 공간 좌표에 테스트 박스를 올려 LiDAR 변화를 만들 수 있습니다. 아래 좌표는 예시이며, 선택한 map에서 로봇 경로와 겹치는 자유 공간으로 바꿉니다.

```bash
ros2 run gazebo_ros spawn_entity.py -entity test_obstacle \
  -file "$(ros2 pkg prefix resilient_amr_bringup)/share/resilient_amr_bringup/models/test_obstacle.sdf" \
  -x 1.5 -y 0.0 -z 0.375
```

박스가 기준 지도상 자유 공간이고 /scan 및 map-to-sensor TF가 정상일 때 메모리에 새 변화로 기록됩니다.

재시작 뒤 `change_memory` 로그에서 복구된 셀 수를 확인하고, 기억 장애물 재관측 전에 A* 경로가 이를 우회하는지 확인합니다. 전체 초기화가 필요할 때:

```bash
ros2 service call /resilient_amr/clear_memory std_srvs/srv/Trigger "{}"
```

## A/B 조건 실행

기준선 A는 저장된 기억을 불러오거나 덮어쓰지 않고, 제안 방식 B는 기억을 사용합니다. 조건별로 같은 시작·목표·장애물 시나리오를 재현하고 `~/.ros/resilient_amr/experiments/run.jsonl`을 보관합니다.

```bash
# A: persistent memory off
ros2 launch resilient_amr_bringup sim.launch.py memory_enabled:=false experiment_condition:=A

# B: persistent memory on
ros2 launch resilient_amr_bringup sim.launch.py memory_enabled:=true experiment_condition:=B
```

## 구성 경계와 주의

- 이 launch는 시뮬레이션 bringup, 기준 map, Nav2, A*, LiDAR 기반 변화 기억, FollowPath 연결을 실행합니다.
- 선반 작업 FSM과 ArUco ID topic은 코드상 연결되어 있습니다. 다만 기본 launch에서는 카메라 detector가 꺼져 있고, 월드의 카메라 토픽·TF·마커 배치·기준 pose를 설정해야 쓸 수 있습니다. 우선은 수동 목적지 topic으로 A* 이동과 기억 재사용을 확인합니다.
- 변화 확정 threshold는 초기 개발값입니다. Gazebo scan 주기와 map 해상도에 맞춰 조정하고 실험 로그에 조건을 남겨야 합니다.
- ArUco 자동 초기화에는 카메라 이미지와 CameraInfo 토픽, map 기준 마커 pose, 올바른 camera-to-base TF가 필요합니다. 기본 TurtleBot3 world에 기준 마커가 포함된다고 가정하지 않습니다.
- A* 셀 장애물 여유 폭은 11 cells (0.05 m/cell 지도에서 약 0.55 m)입니다. Nav2 전역 costmap의 0.55 m inflation과 맞춰 경로가 controller 안전 여유보다 장애물에 가까이 붙지 않도록 합니다. map 해상도나 TurtleBot3 footprint가 다르면 조정합니다.
- Nav2 controller의 로컬 costmap/충돌 안전 기능은 활성화 상태로 두고, 현재 A* 구현은 point-cell 경로라 footprint/inflation 및 동적 장애물 조건을 Gazebo에서 확인해야 합니다.
- 이번 반복 검증은 headless로 수행했습니다. RViz는 기본 비활성화되어 있으며, GUI 렌더링은 이 결과만으로 동작을 보증하지 않습니다.
- ROS 2 Humble/Gazebo Classic 밖의 조합은 turtlebot3/Nav2 launch 인자와 패키지 경로를 조정해야 합니다.
