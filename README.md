# RESILIENT-AMR A*: 장애물 변화 기억과 경로 재사용

TurtleBot3의 A* 경로 계획을 고도화하고, 환경에서 발견한 장애물 변화를 저장해 다음 작업에서도 재사용하는 개인 프로젝트입니다.

통합 시스템 전체 구조, ROS 2 노드와 인터페이스, 환경 변화 검증, 물류 임무 FSM 및 A/B 실험 설계는 [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md)를 참고하세요. 이 문서는 현재 구현 상태와 구분되는 팀 검토용 설계안입니다.

Ubuntu VM에서 Gazebo/Nav2를 실행하는 ROS 2 패키지 구성과 launch 사용법은 [ros2_ws/src/resilient_amr_bringup/README.md](ros2_ws/src/resilient_amr_bringup/README.md)를 참고하세요.

## 프로젝트 목표

- 기본 지도를 기준으로 보존하고, 환경 변화 정보는 별도 레이어로 관리합니다.
- 장애물/빈 공간 관측을 누적해 일시적인 변화와 지속적인 변화를 구분합니다.
- 검증된 장애물은 저장하고, 로봇이나 프로그램을 다시 시작해도 경로 계획에 재사용합니다.
- 장애물이 사라진 뒤 빈 공간 관측이 충분하면 저장한 장애물 정보를 갱신합니다.

이 프로젝트에서 “학습”은 신경망 학습이 아니라 **반복 관측으로 환경 변화를 확인하고 지속 메모리에 반영하는 과정**입니다.

## 현재 구현 상태 — 먼저 확인할 점

현재 GitHub 저장소에는 Python 격자 프로토타입이 있습니다.

- `src/resilient_amr/astar.py`: A* 격자 경로 탐색
- `src/resilient_amr/obstacle_memory.py`: 관측 누적, 장애물 확정/해제, JSON 저장 및 복구
- `src/resilient_amr/demo.py`: 격자 예제 실행
- `tests/test_navigation_memory.py`: 알고리즘과 장애물 기억의 단위 테스트

ROS 2 Humble용 bringup 패키지와 Gazebo/Nav2 launch, OccupancyGrid 변환, LiDAR 변화 메모리 노드, A* Path 노드, Nav2 FollowPath 연결, ArUco·임무 FSM·실험 로거를 추가했습니다. **이 구성은 Ubuntu VM에서 아직 빌드·Gazebo 검증하지 않았습니다.** ArUco 초기화는 카메라와 기준 마커 pose 설정이 필요하며, 셀 단위 A* 경로와 footprint 처리는 Gazebo에서 확인해야 합니다.

## 학원 PC에서 GitHub 저장소 받기

학원 PC에서 GitHub에 로그인한 뒤 터미널을 열고 저장소를 클론합니다. 아래 HTTPS 주소는 저장소 주소입니다.

```bash
git clone https://github.com/waterhyunsu/resilient-amr-astar.git
cd resilient-amr-astar
```

저장소가 비공개라면 학원 PC에서도 해당 GitHub 계정에 저장소 접근 권한이 있어야 합니다. 인증 창이 뜨면 브라우저 로그인 또는 GitHub CLI 인증을 완료합니다. 맥에서 한 로그인이 학원 PC에 자동으로 적용되지는 않습니다.

## 1단계: ROS와 무관한 Python 프로토타입 확인

현재 코드는 Python 3.10 이상과 표준 라이브러리만 사용합니다. 별도 pip 패키지는 필요하지 않습니다.

```bash
python3 --version
python3 -m src.resilient_amr.demo
python3 -m unittest discover -s tests -v
```

데모는 A*가 격자 장애물을 피해 경로를 찾고, 기억 데이터를 `artifacts/environment_memory.json`에 저장합니다. 테스트는 A* 경로와 코너 통과 방지, 장애물 변화 확정/해제, 저장 후 복구를 확인합니다. `artifacts/`의 실행 결과는 Git에 올리지 않습니다.

## 2단계: 학원 PC의 기존 ROS 2/Gazebo 환경 기준선 확인

학원 PC에서 이미 동작하는 ROS 2와 Gazebo 환경을 사용합니다. 먼저 터미널에서 배포판과 설치된 패키지를 확인합니다.

```bash
echo "$ROS_DISTRO"
echo "$TURTLEBOT3_MODEL"
ros2 pkg list | grep -E 'turtlebot3_(gazebo|navigation2)'
```

환경 설정이 필요한 터미널에서는 학원 PC의 설치 버전에 맞춰 ROS 환경을 불러옵니다. 예를 들어 Humble이면:

```bash
source /opt/ros/humble/setup.bash
```

학원에서 사용하는 TurtleBot3 모델과 월드에 맞춰 설정합니다. 공식 TurtleBot3 World 예시의 모델은 `waffle`입니다. 학원 설정이 다르면 강의 자료나 이미 정상 동작하는 실행 명령을 우선합니다.

```bash
export TURTLEBOT3_MODEL=waffle
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

Gazebo가 뜨면 새 터미널에서도 ROS 환경과 모델을 설정한 뒤, 학원에서 제공한 **해당 월드와 일치하는 지도**로 Nav2를 실행합니다. `MAP_YAML`은 실제 지도 파일 경로로 바꿉니다.

```bash
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=waffle
ros2 launch turtlebot3_navigation2 navigation2.launch.py \
  use_sim_time:=True map:=/실제/지도/경로/map.yaml
```

지도 파일이 없다면 SLAM으로 해당 월드를 한 번 매핑하고 저장할 수 있습니다. A* 변화 기억 시험을 위해 기준 지도를 준비한 뒤에는 **새 장애물을 넣은 상태로 기준 지도를 덮어써 저장하지 않습니다.**

## 학원 PC에서 진행할 시험 순서

1. **기준선:** 장애물을 추가하지 않은 월드와 대응 지도로 Nav2 주행이 되는지 확인하고 시작점·목표점을 기록합니다.
2. **기본 장애물 회피:** 기준 경로 위에 Gazebo 기둥 하나를 추가해 Nav2가 멈추거나 우회하는지 확인합니다. 이 단계는 Nav2의 기존 실시간 회피 확인입니다.
3. **통합 bringup:** ROS 패키지를 빌드하고 `resilient_amr_bringup sim.launch.py`로 Gazebo, Nav2, A*, 변화 기억 노드를 실행합니다. `/map`, `/scan`, TF, `/follow_path` 연결을 확인합니다.
4. **변화 확정 및 저장:** 반복 관측된 새 기둥이 별도 환경 기억 파일/지도 레이어에 저장되는지 확인합니다.
5. **재시작 재사용:** 로봇 노드와 Nav2를 재시작하고 같은 기준 지도를 불러옵니다. LiDAR가 기둥을 다시 보기 전에 저장된 변화 정보만으로 자체 A* 전역 경로가 바뀌는지 확인합니다.
6. **장애물 제거 및 기억 갱신:** Gazebo 기둥을 제거하고 해당 위치의 빈 공간을 충분히 관측한 다음 저장 정보가 해제되는지, 후속 경로가 그 구간을 사용할 수 있는지 확인합니다.

**핵심 성공 기준은 2번의 즉시 회피가 아니라 5번의 재시작 후 기억 재사용입니다.** 제거 시험에서는 실제로 해당 위치를 관측하기 전까지 메모리가 성급히 지워지지 않는지도 확인합니다.

## ROS 2 통합 설계 메모

- 지도 입력: `/map` (`nav_msgs/msg/OccupancyGrid`)
- 센서 입력: `/scan` (`sensor_msgs/msg/LaserScan`), TF2
- 목표 주행: 자체 A*가 `nav_msgs/Path`를 만들고 Nav2 `FollowPath` 액션이 추종
- 좌표 기준: `map` 프레임, 거리 m, 각도 rad
- 변화 정보는 기준 지도와 분리하고, 자체 A* 전역 경로에 합쳐서 반영합니다. Nav2 기본 global planner는 이 경로 생성에 사용하지 않습니다.
- A* 엔진은 ROS 메시지 처리와 분리하고, ROS 어댑터가 지도/센서 데이터를 변환하는 방향입니다.
- Nav2 local costmap/controller는 실시간 충돌 안전을 담당하고, 저장된 변화는 A*가 전역 경로 계산에 반영합니다.

## 다음 검증 작업

1. 학원 PC의 ROS 2 배포판, 모델, 월드, 기준 지도 경로를 기록합니다.
2. ROS 2 지도와 격자 A* 사이의 해상도·원점·좌표 변환이 실제 PC map에서도 맞는지 확인합니다.
3. LiDAR와 TF 기반 관측으로 메모리가 확정·저장되는지 확인합니다.
4. 메모리 오버레이가 자체 A* 경로에 반영되는지, 재시작 후 재사용 및 장애물 제거 후 해제되는지 확인합니다.

ROS 지도 좌표 변환과 ROS 연결 코드는 추가되어 있습니다. 학원 PC VM에서 colcon 빌드 및 Gazebo 통합 검증 전에는 실제 시뮬레이션 성공으로 간주하지 않습니다.

## 범위 밖

초기 목표에는 YOLO, 웹 대시보드, 물품 DB, 로봇팔, 다중 로봇, 실물 주행 안전 인증이 포함되지 않습니다. 격자 데모만으로 실제 로봇 주행의 안전성을 보장하지 않습니다.
