"""Run a save/reload/replan example for persistent obstacle changes."""

from pathlib import Path

from .astar import AStarPlanner
from .grid import Cell, Grid
from .obstacle_memory import ObstacleMemory

BASE_MAP = """
####################
#..................#
#..................#
#......####........#
#..................#
#..................#
#..................#
#..............##..#
#..................#
#..................#
#..................#
####################
"""


def main() -> None:
    grid = Grid.from_ascii(BASE_MAP)
    start, goal = (1, 1), (18, 10)
    memory_file = Path("artifacts/environment_memory.json")
    planner = AStarPlanner()
    memory = ObstacleMemory(grid.width, grid.height, confirm_observations=3, clear_observations=3)

    first_path = planner.plan(grid, start, goal, memory.confirmed_cells)
    print(f"기본 지도 경로: {len(first_path)} cells")
    changed_obstacle: Cell = first_path[len(first_path) // 2]
    print(f"원래 경로 위에 새 장애물을 배치합니다: {changed_obstacle}")

    print("새 장애물을 3회 관측해 변화로 확정합니다.")
    for _ in range(memory.confirm_observations):
        memory.observe_occupied(changed_obstacle)
    memory.save(memory_file)
    print(f"변화 지도 저장: {memory_file}")

    restored = ObstacleMemory.load(memory_file, grid)
    updated_path = planner.plan(grid, start, goal, restored.confirmed_cells)
    print(f"저장 후 불러온 경로: {len(updated_path)} cells")
    if changed_obstacle in updated_path:
        raise RuntimeError("replanned path unexpectedly crosses the confirmed obstacle")
    print("# = 기본 장애물, X = 기억된 장애물, * = 새 경로")
    print(grid.render(updated_path, restored.confirmed_cells))

    print("장애물이 실제로 사라진 것을 3회 관측해 기억을 갱신합니다.")
    for _ in range(restored.clear_observations):
        restored.observe_free(changed_obstacle)
    restored.save(memory_file)
    print(f"갱신된 기억 셀 수: {len(restored.confirmed_cells)}")


if __name__ == "__main__":
    main()
