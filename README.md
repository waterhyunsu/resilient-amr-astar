# RESILIENT-AMR A*: 장애물 변화 기억과 경로 재사용

TurtleBot3의 A* 전역 경로 계획에 반복 관측 기반 환경 변화 기억을 더하는 프로젝트입니다. 기준 지도는 보존하고, 지속성이 확인된 장애물 변화를 별도 메모리에 저장해 재시작 뒤 경로 계획에 재사용하는 것을 목표로 합니다.

## 현재 상태

- Python 격자 프로토타입과 장애물 기억 저장·복구 기능이 있습니다.
- ROS 2 Humble, Gazebo Classic 11, TurtleBot3 Waffle, Nav2 통합을 Ubuntu 22.04 WSL2에서 headless로 빌드하고 실행했습니다.
- `/map`, `/scan`, TF, Nav2 `/follow_path`, 자체 A* 경로 주행, 장애물 기억의 저장·재시작 복원·제거를 확인했습니다.
- 반복 A/B 비교는 고정/고분산 조건의 일시적 장애물 각 30쌍, 지속적 장애물 각 60쌍을 완료했습니다. 지속 장애물에서 제안 방식의 재계획 감소 가설은 신뢰구간이 넓어 입증되지 않았습니다. 일부 임무는 Nav2 progress 검사 실패로 중단됐습니다.
- 결과에는 실패도 포함되어 있습니다. 성공 기준, 한계, 신뢰구간, 재현 방법은 [검증 보고서](docs/VALIDATION_REPORT_2026-10-20.md), 실험 설계는 [실험 프로토콜](docs/EXPERIMENT_PROTOCOL.md), 원자료와 분석 파일은 [검증 데이터](docs/validation-data/2026-10-20/)를 참고하세요.

GUI RViz 및 Gazebo 렌더링은 검증 범위에 포함하지 않았습니다. Windows 네이티브 ROS 환경도 검증하지 않았습니다. 재현 대상은 Ubuntu 22.04 WSL2의 ROS 2 Humble/Gazebo Classic 환경입니다.

## 구성

- `src/resilient_amr/astar.py`: ROS 독립 A* 격자 탐색
- `src/resilient_amr/obstacle_memory.py`: 반복 관측, 장애물 확정/해제, JSON 저장 및 복구
- `ros2_ws/src/resilient_amr_bringup/`: ROS 2 노드, launch, Nav2 연동
- `tests/`: Python 단위 테스트
- `docs/experiment_assets/`: 반복 시뮬레이션 실행·분석 도구와 시험 world/map
- `docs/validation-data/`: 원시 로그, 계측값, manifest와 요약

## 빠른 시작: Python 프로토타입

Python 3.10 이상과 표준 라이브러리가 필요합니다.

```bash
python3 -m src.resilient_amr.demo
python3 -m unittest discover -s tests -v
```

## ROS 2 / Gazebo 시뮬레이션

Ubuntu 22.04 WSL2에서 ROS 2 Humble, Gazebo Classic, TurtleBot3 Gazebo/Nav2 패키지가 설치되어 있어야 합니다. 환경 설치 안내는 [ROS 2 bringup 문서](ros2_ws/src/resilient_amr_bringup/README.md)를 확인하세요.

```bash
git clone https://github.com/waterhyunsu/resilient-amr-astar.git
cd resilient-amr-astar/ros2_ws
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=waffle
colcon build --symlink-install
source install/setup.bash
ros2 launch resilient_amr_bringup sim.launch.py
```

현재 기본 실행은 RViz를 띄우지 않습니다. 별도 터미널에서 ROS 환경과 workspace setup을 불러온 뒤 `/map`, `/scan`, TF 및 `/follow_path`를 확인하고, 초기 위치 추정 후 목표를 지정합니다. 전체 절차와 장애물 기억 시험 명령은 bringup 문서에 있습니다.

## 핵심 동작

LiDAR와 TF 관측으로 변경 후보를 누적하고, 검증된 환경 변화는 기준 지도와 분리해 저장합니다. 자체 A*가 변경 정보를 반영해 `nav_msgs/Path`를 만들고 Nav2 `FollowPath` 액션이 경로를 추종합니다. Nav2 local costmap과 controller는 주행 중 충돌 안전을 담당합니다. 이 프로젝트의 “학습”은 신경망 훈련이 아니라 반복 관측으로 환경 변화를 확인하고 지속 메모리에 반영하는 과정입니다.

통합 시스템 구상과 노드 관계는 [시스템 설계 문서](docs/SYSTEM_DESIGN.md)를 참고하세요. 설계 문서의 계획 항목은 현재 동작이 검증된 기능과 구분해서 읽어야 합니다.
