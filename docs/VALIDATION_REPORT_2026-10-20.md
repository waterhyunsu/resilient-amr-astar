# ROS 2 / TurtleBot3 시뮬레이션 검증 보고서

작성일: 2026-10-21  
저장소 기준 커밋: `dd85cd293c490cb1170ac74565ed27cc7fe501ad` (`main`)  
실행 환경: Windows 11 호스트의 Ubuntu 22.04 WSL2

## 1. 결론

ROS 2 Humble, Gazebo Classic, TurtleBot3 Waffle 및 Nav2를 WSL2에서 실행하고 A* 경로 계획, Nav2 FollowPath 주행, 장애물 기억 저장, 시뮬레이터 재시작 후 기억 복원, 장애물 제거 후 주변 기억 셀 제거까지 반복 시험했습니다. 일반 주행과 기억 기능은 반복해서 확인됐습니다.

비교 실험의 핵심 가설인 “B가 영구 장애물 조건에서 A보다 재계획을 줄인다”는 통계적으로 입증되지 않았습니다. 고정 조건과 고분산 조건 모두 최대 60쌍까지 확장했지만 paired 재계획 차이의 95% 신뢰구간이 0을 포함하고, 사전 기준인 반폭 0.5회보다 넓었습니다. 사용자가 허용한 2배 확장 한도까지 수행했으며, 결과를 유리한 방향으로 단정하지 않습니다.

장애물 주변 기억 셀의 재시작 복원은 B 60/60회, 제거 단계 종료 시 주변 셀 0은 고분산 영구 조건에서 60/60회 확인됐습니다. 다만 일부 Nav2 주행은 `Failed to make progress`로 중단됐습니다. 기억 제거 확인과 목적지까지의 복귀 주행 성공은 별개의 결과입니다.

## 2. 호스트 및 ROS 환경

- Windows 11 Home x64 호스트에서 Ubuntu 22.04.5 WSL2의 bash를 사용했습니다. VirtualBox, 별도 VM, 다른 WSL 배포판, Mac UTM은 사용하지 않았습니다. Terminator는 설치돼 있지만 이 검증은 headless로 수행했습니다.
- Ubuntu 측 구성: ROS 2 Humble, Python 3.10.12, colcon-core 0.21.3, Gazebo Classic 11.10.2, `gazebo_ros_pkgs` 3.9.0, TurtleBot3 Gazebo 2.3.8, TurtleBot3 Navigation2 2.3.6, Nav2 bringup 1.1.20.
- 저장소: `<REPO_ROOT>`; 기존 checkout을 덮어쓰지 않고 사용했습니다.
- Windows 네이티브에는 `ros2`, `colcon`, `gz`가 없고 WSL Ubuntu에 필요한 ROS/Gazebo 설치가 있었습니다. 시스템 패키지를 새로 설치하거나 관리자 설정을 바꾸지 않았습니다.
- 실험은 `ROS_DOMAIN_ID=57`, `TURTLEBOT3_MODEL=waffle`로 수행했습니다. 빌드 결과는 `/tmp/resilient-amr-install2` 아래에 두었습니다.

## 3. 코드 변경 및 기본 확인

수정한 주요 파일은 다음과 같습니다.

- `ros2_ws/src/resilient_amr_bringup/launch/sim.launch.py`: Humble/Nav2 파라미터와 기억·실험 로그 경로 연결, RViz 기본 비활성화.
- `ros2_ws/src/resilient_amr_bringup/resilient_amr_bringup/change_memory.py`: scan 시각의 TF가 오래된 경우를 피하도록 최신 TF 기반 관측 처리.
- `.../astar_planner.py`, `.../map_utils.py`, `.../change_memory.py`: 기억 셀 추가·삭제 시 지도와 현재 경로 연계 처리, 점유 셀 팽창 계산 개선.
- `.../path_follower.py`, `src/resilient_amr/path_geometry.py`: 활성 FollowPath 경로와 새 경로를 비교해 의미 있는 경로 변경 때만 action goal을 교체하도록 조정했습니다. 이 수정 후 시험에서 FollowPath 취소 평균은 0이었습니다.
- `.../experiment_logger.py`, `tests/test_navigation_memory.py`: 임무·경로·오도메트리 계측 및 회귀 시험.
- `docs/experiment_assets/`: 반복 Gazebo 실험 실행기, 분석기, arena 및 Nav2 시험 설정.
- `docs/EXPERIMENT_PROTOCOL.md`: 비교 설계와 사전 정밀도 확장 규칙.

확인 결과:

- `python3 -m unittest discover -s tests -v`: 14개 단위 시험 통과.
- `python3 -m py_compile` 대상 코드와 실험 스크립트 통과.
- 격자 데모에서 A* 경로, 기억 저장·불러오기, 장애물 변경 후 재계획·해제를 확인했습니다.
- 격리된 `colcon build` 성공. ROS 그래프에서 `/map`, `/scan`, `/odom`, `/tf`, `map -> base_footprint`, Nav2 `/follow_path` 서버 및 A* 경로의 실제 주행을 확인했습니다.
- GUI RViz/gzclient 렌더링은 이번 headless 검증 범위에 포함하지 않았습니다.

## 4. 반복 설계와 표본 수

A와 B는 동일한 A*, Nav2, 로봇 및 안전 설정을 사용하며 장애물 정보 처리 정책만 다르게 비교했습니다. A/B 실행 순서는 페어마다 무작위화했고, 각 실행은 Gazebo/ROS/Nav2를 cold start했습니다. 실패 실행은 성공률 분모에서 제외하지 않았습니다.

| 실험 블록 | 조건별 A/B paired 반복 | 환경 |
|---|---:|---|
| 고정 조건, transient | 30쌍 | 시작·목표·장애물·시간 고정 |
| 고정 조건, persistent | 60쌍 | 원래 30쌍에서 정밀도 부족, seed 31–60으로 30쌍 추가 |
| 고분산, transient | 30쌍 | 시작·목표·장애물 위치 및 이벤트 시점 변화 |
| 고분산, persistent | 60쌍 | 원래 30쌍에서 정밀도 부족, 고유 seed 31–60으로 30쌍 추가 |

총 180 paired A/B 반복이며, transient 60쌍과 persistent 120쌍입니다. persistent 페어는 arm별 임무, 재시작 재사용, 장애물 제거의 세 cold-start 단계를 거칩니다. 전체 계측 단계는 840회입니다. 반복 단위, 메트릭 정의, 사전 확장 규칙은 [실험 프로토콜](EXPERIMENT_PROTOCOL.md)에 기록했습니다.

## 5. 주요 결과

### 고정 조건

고정 조건 persistent 60쌍의 주요 비교는 B−A 재계획 차이 `−1.23회`, 95% bootstrap CI `[-4.57, 2.25]`입니다. success 차이는 `+0.033`이며 CI `[0.000, 0.083]`입니다. 신뢰구간이 넓고 재계획 CI가 0을 포함하므로 재계획 감소를 입증하지 못했습니다.

고정 transient 30쌍은 재계획 차이 `−0.23회`, CI `[-0.43, -0.03]`; A/B 성공은 모두 30/30입니다. 정밀도 규칙은 충족했지만, 이 한 조건의 값만으로 일반적 효과나 유의성을 주장하지 않습니다.

### 고분산 조건

고분산 persistent는 고유 seed 1–60으로 60쌍 완료했습니다. 재시작 재사용 단계의 B−A 재계획 차이는 `−2.40회`, 95% CI `[-5.22, 0.42]`이며 성공률 차이는 `0.000`, CI `[-0.050, 0.050]`입니다. CI가 0을 포함하고 재계획 CI 반폭은 2.82회라 사전 기준을 충족하지 못했습니다. 60쌍 상한에 도달했으므로 추가 반복은 하지 않았고, 불확실한 결과로 보고합니다.

고분산 transient 30쌍은 재계획 차이 `0.00회`, CI `[-0.13, 0.13]`; 성공은 A 29/30, B 30/30입니다. 재계획 지표의 사전 정밀도 기준은 충족했습니다.

| 고분산 persistent 단계 | A 성공 | B 성공 | B 기억 복원 |
|---|---:|---:|---:|
| obstacle mission | 60/60 | 60/60 | — |
| after restart / reuse | 59/60 | 59/60 | 60/60 |
| obstacle removal mission | 60/60 | 58/60 | 60/60 |

B의 장애물 제거 단계는 60/60에서 장애물 주변 기억 셀이 0으로 기록됐습니다. 두 건의 B 제거 단계 주행 실패에서도 기억 주변 셀 제거는 기록됐지만 로봇이 목표에 도달하지 못했습니다.

## 6. 실패와 한계

정상 데이터에서 10개 실패 단계가 기록됐습니다. 고정 조건 5건, 고분산 조건 5건입니다. 반복 로그의 공통적인 직접 실패 신호는 Nav2 controller `Failed to make progress` 및 FollowPath abort입니다. 일부에서는 `Transform data too old when converting from map to odom`이 반복돼 함께 기록됐습니다. 이 로그는 controller/TF 경로의 실패를 보여주지만, TF 지연이 모든 실패의 단일 근본 원인이라고 증명하지는 않습니다.

- 고분산 B persistent seed 18, restart/reuse: `map -> odom` TF가 오래됐다는 오류 153회, 뒤이어 controller progress 실패와 FollowPath abort.
- 고분산 A persistent seed 31, restart/reuse: 오래된 TF 오류 361회, controller progress 실패와 FollowPath abort.
- 고분산 A transient seed 25, mission: controller progress 실패와 FollowPath abort. 목표와 반대 방향으로 이탈한 기록이 포함됩니다.
- 고분산 B persistent seed 42 및 52, obstacle removal: controller progress 실패와 FollowPath abort. 기억 주변 셀은 0으로 정리됐지만 주행은 실패했습니다.
- 고정 조건 실패도 controller progress/FollowPath abort가 주 신호였고, 일부 A 재시작 실패에서 오래된 TF 경고가 반복됐습니다.

재계획 차이의 분산이 커서 60쌍으로도 정밀도 기준을 충족하지 못했습니다. 장애물 제거 단계는 로봇이 과거 장애물 위치를 얼마나 재관측하느냐에 따라 종료 시점의 잔여 기억량이 달라질 수 있습니다. 환경 변화 판별의 precision/recall과 반영 시간은 현재 계측으로 완전한 정량 검증을 하지 못했습니다. 성능 가설은 미입증이며, 향후에는 TF 시간 동기화와 Nav2 progress abort 빈도, 제거 관측 시간/coverage를 별도 지표로 개선·계측해야 합니다.

## 7. 데이터와 재현

원시 JSONL, ROS 로그, launch 로그, 메모리 스냅샷 및 manifest는 [validation-data/2026-10-20](validation-data/2026-10-20)에 보존했습니다.

- 고정 persistent 합산 60쌍 요약: [summary-combined-60.md](validation-data/2026-10-20/repeat-fixed-20261020T091155Z/summary-combined-60.md)
- 고분산 persistent 합산 60쌍 요약: [summary-high-variance-combined-60.md](validation-data/2026-10-20/repeat-high_variance-persistent-20261020T140500Z/summary-high-variance-combined-60.md)
- 고분산 초기 30쌍 요약: [summary.md](validation-data/2026-10-20/repeat-high_variance-20261020T111326Z/summary.md)

재현 기본 환경:

```bash
source /opt/ros/humble/setup.bash
source /tmp/resilient-amr-install2/setup.bash
export TURTLEBOT3_MODEL=waffle ROS_DOMAIN_ID=57
cd /path/to/resilient-amr-astar
```

단계별 반복 실행 예:

```bash
python3 docs/experiment_assets/run_experiments.py --phase fixed --count 30
python3 docs/experiment_assets/run_experiments.py --phase fixed --count 30 --scenarios persistent --seed-offset 31
python3 docs/experiment_assets/run_experiments.py --phase high_variance --count 30
python3 docs/experiment_assets/run_experiments.py --phase high_variance --count 30 --scenarios persistent --seed-offset 31
```

두 번의 중간 확장 시도 폴더(`repeat-high_variance-20261020T135636Z`, `repeat-high_variance-20261020T135851Z`)는 seed 중복 및 이전 인터럽트에서 남은 프로세스에 의한 오염 때문에 추론 분석에서 제외했습니다. 폴더와 로그는 삭제하지 않고 보존했습니다. 최종 분석은 고유 seed 1–30과 31–60의 완료 manifest만 사용했습니다.

## 8. 검토 및 Git 상태

코드, 문서, 프로토콜 및 결과 데이터가 작업 폴더에 있습니다. Git commit 또는 push는 하지 않았습니다. 검토 대상은 이 보고서와 변경 파일 및 원자료입니다. 사용자 검토와 명시적 승인 전에는 commit/push하지 않습니다.
