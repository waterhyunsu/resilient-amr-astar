import tempfile
import unittest
from pathlib import Path

from src.resilient_amr.astar import AStarPlanner
from src.resilient_amr.grid import Grid
from src.resilient_amr.obstacle_memory import ObstacleMemory
from src.resilient_amr.path_geometry import paths_are_equivalent
from src.resilient_amr.path_geometry import paths_are_equivalent


class AStarTests(unittest.TestCase):
    def test_finds_path_and_avoids_remembered_obstacle(self):
        grid = Grid.from_ascii("""
.....
.....
.....
""")
        blocked = {(2, 1)}
        path = AStarPlanner().plan(grid, (0, 1), (4, 1), blocked)
        self.assertTrue(path)
        self.assertNotIn((2, 1), path)
        self.assertEqual(path[0], (0, 1))
        self.assertEqual(path[-1], (4, 1))

    def test_does_not_cut_diagonal_corner(self):
        grid = Grid.from_ascii("""
.#
#.
""")
        self.assertEqual(AStarPlanner().plan(grid, (0, 0), (1, 1)), [])

    def test_dynamic_obstacle_at_start_can_be_escaped_when_enabled(self):
        grid = Grid.from_ascii("""
.....
.....
.....
""")
        observed = {(0, 1)}
        self.assertEqual(AStarPlanner().plan(grid, (0, 1), (4, 1), observed), [])
        path = AStarPlanner().plan(grid, (0, 1), (4, 1), observed,
                                   allow_blocked_start=True)
        self.assertTrue(path)
        self.assertEqual(path[0], (0, 1))
        self.assertEqual(path[-1], (4, 1))

    def test_dynamic_escape_does_not_override_static_map_obstacle(self):
        grid = Grid.from_ascii("""
#....
.....
.....
""")
        self.assertEqual(AStarPlanner().plan(grid, (0, 0), (4, 0), {(0, 0)},
                                             allow_blocked_start=True), [])

    def test_dynamic_escape_can_leave_inflation_halo_but_not_raw_hit(self):
        grid = Grid.from_ascii("""
        .......
        .......
        .......
        .......
        .......
        """)
        raw_hit = (1, 2)
        inflated = {(x, y) for x in range(0, 3) for y in range(1, 4)}
        start, goal = (0, 2), (6, 2)
        escape_halo = inflated - {raw_hit}
        path = AStarPlanner().plan(grid, start, goal, inflated,
                                   allow_blocked_start=True, escape_cells=escape_halo)
        self.assertTrue(path)
        self.assertEqual(path[0], start)
        self.assertEqual(path[-1], goal)
        self.assertNotIn(raw_hit, path)

    def test_dynamic_escape_does_not_cross_confirmed_memory(self):
        grid = Grid.from_ascii("""
        .......
        .......
        .......
        """)
        confirmed = {(1, 1)}
        escape_halo = {(0, 1), (0, 0), (1, 0)}
        path = AStarPlanner().plan(grid, (0, 1), (4, 1), confirmed | escape_halo,
                                   allow_blocked_start=True, escape_cells=escape_halo)
        self.assertTrue(path)
        self.assertNotIn((1, 1), path)

    def test_current_pose_can_leave_confirmed_memory_inflation_halo(self):
        grid = Grid.from_ascii("""
        .......
        .......
        .......
        .......
        .......
        """)
        confirmed = {(1, 2)}
        inflated = {(x, y) for x in range(0, 3) for y in range(1, 4)}
        escape_halo = inflated - confirmed
        path = AStarPlanner().plan(grid, (0, 2), (6, 2), inflated,
                                   allow_blocked_start=True, escape_cells=escape_halo)
        self.assertTrue(path)
        self.assertEqual(path[0], (0, 2))
        self.assertEqual(path[-1], (6, 2))
        self.assertNotIn((1, 2), path)

    def test_escape_halo_cannot_cross_confirmed_wall(self):
        grid = Grid.from_ascii("""
        .....
        .....
        .....
        """)
        confirmed = {(1, y) for y in range(3)}
        soft = confirmed | {(0, 1), (2, 1)}
        self.assertEqual(AStarPlanner().plan(grid, (0, 1), (4, 1), soft,
                                             allow_blocked_start=True,
                                             escape_cells={(0, 1)}), [])


class ObstacleMemoryTests(unittest.TestCase):
    def setUp(self):
        self.grid = Grid.from_ascii("""
....
....
....
""")
        self.memory = ObstacleMemory(4, 3, confirm_observations=3, clear_observations=2)

    def test_change_requires_repeated_observation_and_can_be_cleared(self):
        cell = (2, 1)
        self.memory.observe_occupied(cell)
        self.memory.observe_occupied(cell)
        self.assertNotIn(cell, self.memory.confirmed_cells)
        self.memory.observe_occupied(cell)
        self.assertIn(cell, self.memory.confirmed_cells)
        self.memory.observe_free(cell)
        self.assertIn(cell, self.memory.confirmed_cells)
        self.memory.observe_free(cell)
        self.assertNotIn(cell, self.memory.confirmed_cells)

    def test_save_reload_reuses_confirmed_obstacle(self):
        cell = (2, 1)
        for _ in range(3):
            self.memory.observe_occupied(cell)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.json"
            self.memory.save(path)
            restored = ObstacleMemory.load(path, self.grid)
        self.assertIn(cell, restored.confirmed_cells)

    def test_rejects_memory_for_different_map_size(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.json"
            self.memory.save(path)
            other_grid = Grid.from_ascii("...\n...")
            with self.assertRaises(ValueError):
                ObstacleMemory.load(path, other_grid)


class PathGeometryTests(unittest.TestCase):
    def test_progress_only_update_keeps_same_route(self):
        old = [(x * 0.1, 0.0) for x in range(31)]
        updated = [(x * 0.1, 0.0) for x in range(10, 31)]
        self.assertTrue(paths_are_equivalent(old, updated))

    def test_material_detour_change_is_not_ignored(self):
        old = [(x * 0.1, 0.4 if 10 <= x <= 20 else 0.0) for x in range(31)]
        updated = [(x * 0.1, -0.4 if 10 <= x <= 20 else 0.0) for x in range(10, 31)]
        self.assertFalse(paths_are_equivalent(old, updated))

    def test_large_start_deviation_is_not_treated_as_progress(self):
        old = [(x * 0.1, 0.0) for x in range(31)]
        updated = [(1.0, 0.5), (1.5, 0.5), (2.0, 0.5), (3.0, 0.5)]
        self.assertFalse(paths_are_equivalent(old, updated))


class PathGeometryTests(unittest.TestCase):
    def test_progress_only_update_keeps_same_route(self):
        old = [(x * 0.1, 0.0) for x in range(31)]
        updated = [(x * 0.1, 0.0) for x in range(10, 31)]
        self.assertTrue(paths_are_equivalent(old, updated))

    def test_material_detour_change_replaces_route(self):
        old = [(x * 0.1, 0.4 if 10 <= x <= 20 else 0.0) for x in range(31)]
        updated = [(x * 0.1, -0.4 if 10 <= x <= 20 else 0.0) for x in range(10, 31)]
        self.assertFalse(paths_are_equivalent(old, updated))

    def test_large_start_deviation_is_not_treated_as_progress(self):
        old = [(x * 0.1, 0.0) for x in range(31)]
        updated = [(1.0, 0.5), (1.5, 0.5), (2.0, 0.5), (3.0, 0.5)]
        self.assertFalse(paths_are_equivalent(old, updated))


if __name__ == "__main__":
    unittest.main()
