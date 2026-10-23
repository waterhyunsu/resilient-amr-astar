# SMART-VISION AMR | RESILIENT-AMR A*

> ROS 2 Humble 기반 TurtleBot3 물류 AMR 팀 프로젝트 — A* 주행, LiDAR 환경 변화 검증 및 변경 지도 재사용

**프로젝트 기간:** 2026.10.19 ~ 2026.11.06 (3주)  
**개발 인원:** 5명  
**대상 플랫폼:** TurtleBot3 / ROS 2 Humble / Ubuntu 22.04  
**현재 저장소의 역할:** 팀 전체 시스템 중 **자율주행·장애물 변화 기억·시뮬레이션 통합을 위한 개발 및 검증 저장소**

> **상태 안내 (2026-10-23):** 이 저장소는 개인 A* 알고리즘 프로토타입에서 출발하여 ROS 2 노드, Launch, Nav2 FollowPath 연동 및 Gazebo 시뮬레이션 실험까지 확장되었습니다. **실제 TurtleBot3 통합은 진행 중**이며, 이 저장소에 팀 전체 기능(ArUco, 선반·물류 임무 관리 등)이 모두 구현되어 있다는 뜻은 아닙니다.

## 1. 팀 프로젝트 목표

[팀 프로젝트 기획서 — 트위니형 자율주행 로봇 구현](https://hyper-hope-f05.notion.site/3fef1b81cbca80119899fd669c81eb66?pvs=74)

작업자가 지정한 선반의 물품을 배송 지점으로 이동시키는 **물류 AMR 프로토타입**을 구축합니다. 일반적인 A* 장애물 회피에 더해, LiDAR로 관측된 환경 변화를 반복 검증하고, 지속성이 확인된 변화만 경로 계획에 재사용하는 방법을 실험합니다.

최종 팀 통합 시나리오:

1. **초기 위치 설정:** 기준 ArUco 마커 검출 → TF2 좌표 변환 → AMCL 위치 초기화
2. **임무 입력:** 작업자가 선반 B(ID 2) 운송 요청 → 등록된 접근 좌표 조회
3. **선반으로 주행:** A* 전역 경로 생성 → Nav2 경로 추종, LiDAR 기반 안전 대응
4. **선반 도착 검증:** ArUco ID 2 확인 → 작업자 수동 적재
5. **배송:** 배송 지점(ID 4)으로 이동 → ArUco 도착 확인 → 수동 하역
6. **환경 적응:** 반복 검증된 장애물 변화를 지도와 분리해 저장하고 후속 임무의 경로 계획에 반영, 제거 시 재검증 후 해제

선반 A/B/C는 각각 **ID 1/2/3**, 배송 지점은 **ID 4**를 사용할 계획입니다. **자동 적재 장치나 로봇팔은 개발 범위에 포함하지 않습니다.**

## 2. 이 저장소에서 다루는 기능

| 영역 | 내용 | 상태 |
|---|---|---|
| A* 격자 경로 계획 | ROS와 독립적인 경로 탐색 프로토타입 | 구현 |
| 장애물 변화 기억 | 반복 관측, 확정·해제, JSON 저장·복원 | 구현 |
| ROS 2 연동 | 센서·지도·TF 입력을 활용한 경로 계획 및 주행 연계 | 시뮬레이션 확인 |
| Nav2 경로 추종 | 자체 A*가 생성한 `nav_msgs/Path`를 `FollowPath` 액션에 전달 | 시뮬레이션 확인 |
| Gazebo / Launch | TurtleBot3 및 Nav2 구성요소 실행 자동화 | WSL2 headless 실행 확인 |
| 실제 TurtleBot3 | 실기기 연결, 센서·주행·네트워크 점검 | 진행 중 / 미검증 항목 존재 |
| ArUco 위치 초기화 및 선반 ID 식별 | 팀 통합 시나리오에 필요한 기능 | 이 저장소에서 완료 여부 미확인 |
| Task Manager / FSM | 선반→배송 지점 임무 상태 관리 | 팀 통합 예정 |

**주의:** 시뮬레이션에서 성공한 기능을 실기기 검증 완료로 해석하지 마세요. 위 상태는 원격 저장소의 2026-10-23 공개 문서 기준입니다. 로컬에서 아직 push하지 않은 수정 사항은 반영되지 않았을 수 있습니다.

## 3. ROS 2 시스템 구성

```text
[Linux PC / ROS 2 Humble]
  ├─ 작업 명령 / Task Manager (팀 통합 예정)
  ├─ ArUco Detector / AMCL 초기화 (팀 통합 예정)
  ├─ /map, /scan, TF 구독
  ├─ Change Detector / Validator
  │    └─ 지속 장애물 후보의 누적 관측 및 검증
  ├─ Obstacle Memory
  │    └─ 확정/해제 상태 저장·복원 (JSON)
  ├─ A* Planner
  │    └─ 기본 지도 + 검증된 장애물 변경 정보 → nav_msgs/Path
  ├─ Nav2 FollowPath
  │    └─ Controller / local costmap → 로봇 속도 명령
  └─ RViz / 로그 분석 (사용 환경에 따라 별도 실행)
               ⇅ ROS 2 DDS / TF2
[TurtleBot3 / Raspberry Pi]
  ├─ LiDAR / 카메라 / Odometry
  └─ 구동부 / 모터 제어
```

- **Topic:** `/map`, `/scan`, TF, 경로 및 로봇 상태 등
- **Action:** Nav2 `/follow_path`로 경로 추종
- **TF2:** `map`·`odom`·`base_link` 등 좌표계 관계
- **역할 분리:** 자체 A*는 **전역 경로 생성**, Nav2 controller/local costmap은 **경로 추종 및 주행 중 장애물 대응**을 담당합니다.
- **지도 정책:** 원본 정적 지도는 보존하고, 검증된 장애물 변경 정보는 별도 계층·저장 데이터로 관리합니다. 이 프로젝트에서 '학습'은 머신러닝 모델 훈련이 아닌 **반복 관측에 따른 상태 검증**을 의미합니다.

상세 설계: [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md)

## 4. 저장소 구조

```text
resilient-amr-astar/
├── README.md
├── HANDOFF.md
├── pyproject.toml
├── src/resilient_amr/
│   ├── astar.py               # ROS 비의존 A* 격자 경로 탐색
│   ├── obstacle_memory.py     # 변화 누적·확정·해제·저장·복원
│   └── demo.py                # Python 프로토타입 실행
├── ros2_ws/src/resilient_amr_bringup/
│   └── ...                    # ROS 2 노드, launch, Nav2 연동
├── tests/                     # Python 단위 테스트
└── docs/
    ├── SYSTEM_DESIGN.md
    ├── EXPERIMENT_PROTOCOL.md
    ├── VALIDATION_REPORT_2026-10-20.md
    ├── experiment_assets/    # 실험용 월드·맵·자동화/분석 도구
    └── validation-data/      # 원시 결과 및 분석 자료
```

파일 목록은 커밋에 따라 변경될 수 있습니다. 실행 옵션과 필요한 패키지는 [ROS 2 Bringup README](ros2_ws/src/resilient_amr_bringup/README.md)에서 확인하세요.

## 5. 개발 환경 및 실행

### A. 순수 Python 프로토타입

Python 3.10 이상에서 저장소 루트 기준:

```bash
python3 -m src.resilient_amr.demo
python3 -m unittest discover -s tests -v
```

### B. Gazebo / ROS 2 시뮬레이션

**기존 확인 환경:** Ubuntu 22.04 WSL2, ROS 2 Humble, Gazebo Classic 11, TurtleBot3 Waffle, Nav2 (headless). GUI RViz/Gazebo 렌더링은 기존 검증 범위가 아닙니다.

```bash
git clone https://github.com/waterhyunsu/resilient-amr-astar.git
cd resilient-amr-astar/ros2_ws
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=waffle
colcon build --symlink-install
source install/setup.bash
ros2 launch resilient_amr_bringup sim.launch.py
```

위 명령은 **시뮬레이션용**입니다. 실제 TurtleBot3에 그대로 실행하는 명령으로 사용하지 마세요. 실기기에서는 Raspberry Pi bringup, 호스트와 로봇의 `ROS_DOMAIN_ID`, 네트워크, 모델, 센서 토픽, TF, Nav2 구성을 별도로 맞춰야 합니다. 검증 전에는 로봇을 안전하게 들어 올리거나 충분한 시험 공간을 확보하고, 비상 정지 수단을 준비하세요.

### C. 실제 TurtleBot3 연동 시 체크

```bash
# Linux PC와 TurtleBot3에서 각각 확인
source /opt/ros/humble/setup.bash
echo "$ROS_DOMAIN_ID"
ros2 node list
ros2 topic list
ros2 topic hz /scan
ros2 topic echo /odom --once
ros2 topic echo /tf --once
ros2 action list
```

- `/scan`, `/odom`, `/tf`, `/map`이 기대한 발행자와 QoS로 제공되는지 확인
- `map → odom → base_link` 좌표계 연결 및 초기 위치 추정 확인
- 제어 노드가 중복으로 `/cmd_vel`을 발행하지 않는지 확인
- Nav2 lifecycle 및 FollowPath action server 준비 상태 확인
- **현장 검증에서 통과한 항목만** 실기기 완료로 기록

## 6. 반복 관측 기반 환경 변화 처리

```text
LiDAR 관측 → 변경 후보 검출 → 누적 관측/지속성 검증
                              ├─ 일시적 변화: 영구 지도에는 미반영
                              └─ 지속적 변화: 장애물 기억 저장
                                              ↓
기본 지도 + 유효한 변화 기억 → A* 재계획 → Nav2 경로 추종
                                              ↓
                         재관측으로 제거 확인 → 기억 해제
```

일반 장애물 회피와의 차이는 **한 번 회피한 장애물의 지속성을 별도로 판단하고, 다음 임무에서도 사용할지 결정**한다는 점입니다. 검증된 변경 정보는 JSON으로 보존·복구할 수 있도록 설계했습니다.

## 7. 실험 결과 및 한계

기존 시뮬레이션에서는 일시 장애물(고정/고분산 조건 각 **30쌍**)과 지속 장애물(각 **60쌍**)의 A/B 비교가 수행되었습니다. 장애물 기억의 저장·재시작 복원·제거 동작은 확인했으나, **지속 장애물에 대해 제안 방식이 재계획 횟수를 줄인다는 가설은 통계적으로 입증되지 않았습니다.** 신뢰구간이 넓었고 일부 임무는 Nav2 progress 검사 실패로 중단되었습니다.

이는 연구 결과를 숨길 이유가 아니라, 조건 통제와 실기기 검증에서 개선해야 할 근거입니다.

- [검증 보고서](docs/VALIDATION_REPORT_2026-10-20.md)
- [실험 프로토콜](docs/EXPERIMENT_PROTOCOL.md)
- [검증 원자료](docs/validation-data/2026-10-20/)

**팀 통합 평가 계획:** 동일한 지도·목표점·장애물 조건에서 기본 A* 장애물 대응 방식과 변경 정보 검증/재사용 방식을 비교합니다. 재계획 횟수, 주행 시간, 이동 거리, 임무 성공률, 지도 반영 지연 및 불필요한 경로 전환을 계측합니다. 기존 수치는 **시뮬레이션 실험 결과**이지 실제 로봇의 성능 수치가 아닙니다.

## 8. 팀 통합 계획

| 기간 | 팀 통합 목표 |
|---|---|
| 10/19–10/23 | ROS 2/Launch 아키텍처, Gazebo, 기본 A*·Nav2, ArUco 초기화 기반 확보 |
| 10/26–10/30 | 선반 마커·임무 흐름, LiDAR 변화 감지/검증, 경로 재계획 연계 |
| 11/02–11/06 | 변경 정보 저장·복원, 실기기 통합, A/B 비교 평가 및 시연 |

본 저장소를 전체 팀 코드의 완성본으로 취급하지 않습니다. 팀원별 구현물을 합칠 때 각 기능의 **노드 이름, 입출력 Topic/Service/Action, 좌표계, 파라미터 및 실행 순서**를 우선 합의해야 합니다.

## 9. 팀원에게 공유

- 현재 팀 프로젝트 요구사항의 기준 문서는 [Notion 통합 기획서](https://hyper-hope-f05.notion.site/3fef1b81cbca80119899fd669c81eb66?pvs=74)입니다.
- 이 GitHub 저장소는 그중 **A*·LiDAR 변화 검증 및 Nav2 실행 구조를 선행 개발한 작업물**입니다.
- `sim.launch.py`는 **시뮬레이션용**이며 실제 로봇용 bringup과 혼동하지 않습니다.
- 통합 후에는 실기기 검증 결과, Launch 명령 및 인터페이스를 README에 갱신합니다.
- 장애물 기억 알고리즘의 성능 향상은 **가설**이며, 현재 실험 결과를 성공으로 포장하지 않습니다.

---

**참고:** 본 프로젝트는 특정 상용 AMR 제품의 공식 구현이 아닌 교육용 프로토타입입니다. 트위니 '나르고'는 프로젝트의 물류 운영 시나리오를 구상할 때 참고한 사례입니다.
