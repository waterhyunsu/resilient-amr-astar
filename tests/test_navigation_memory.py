import tempfile
import unittest
from pathlib import Path

from src.resilient_amr.astar import AStarPlanner
from src.resilient_amr.grid import Grid
from src.resilient_amr.obstacle_memory import ObstacleMemory


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


if __name__ == "__main__":
    unittest.main()
