import unittest
import sys
import os
import math

# Добавляем путь к скомпилированной библиотеке
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../build')))

try:
    import pathfinding_core as pfc
except ImportError:
    raise ImportError("Не найден модуль pathfinding_core. Сначала соберите проект через CMake.")

class TestPathPlanner(unittest.TestCase):
    
    def setUp(self):
        """Подготовка перед каждым тестом"""
        pass

    def create_planner(self, grid_str, width, height):
        """Вспомогательный метод для создания планировщика из строки"""
        # Преобразуем строку вида ".#.." в список [0, 1, 0, 0]
        grid = []
        for char in grid_str:
            if char in ['.', 'S', 'G']:
                grid.append(0)
            elif char in ['#', '@']:
                grid.append(1)
        return pfc.PathPlanner(width, height, grid)

    def test_simple_path_bfs(self):
        """Проверка простого пути BFS на пустой карте"""
        # Карта 5x1: S . . . G
        grid_str = "S...G"
        planner = self.create_planner(grid_str, 5, 1)
        
        res = planner.find_path(0, 0, 4, 0, pfc.AlgorithmType.BFS)
        
        self.assertTrue(res.found, "Путь должен быть найден")
        self.assertEqual(len(res.path), 5, "Путь должен содержать 5 точек")
        self.assertEqual(res.path[0], (0, 0))
        self.assertEqual(res.path[-1], (4, 0))

    def test_obstacle_avoidance(self):
        """Проверка обхода препятствия"""
        # S # G
        # . . .
        # Стенка между S и G, нужно обойти снизу.
        # Оптимальный путь: (0,0) -> (0,1) -> (1,1) -> (2,1) -> (2,0)
        grid_str = "S#G..."
        planner = self.create_planner(grid_str, 3, 2)
        
        res = planner.find_path(0, 0, 2, 0, pfc.AlgorithmType.AStar, pfc.HeuristicType.Manhattan)
        
        self.assertTrue(res.found)
        # Длина должна быть больше, чем по прямой (2.0)
        self.assertGreater(res.path_length, 2.0)

    def test_no_path(self):
        """Проверка случая, когда пути нет"""
        # S # G
        # # # #
        # Цель полностью изолирована
        grid_str = "S#G###" 
        planner = self.create_planner(grid_str, 3, 2)
        
        res = planner.find_path(0, 0, 2, 0, pfc.AlgorithmType.BFS)
        
        self.assertFalse(res.found, "Путь не должен быть найден")
        self.assertEqual(res.path_length, 0.0)

    def test_corner_cutting_strict(self):
        """
        Проверка запрета срезания углов (Corner Cutting).
        Требование задания : диагональный переход разрешён ТОЛЬКО если 
        обе ортогональные клетки свободны.
        
        Карта 2x2:
        . #   (0,0) (1,0) - стена справа
        # G   (0,1) (1,1) - стена снизу, цель по диагонали
        
        Из (0,0) в (1,1) попасть НЕЛЬЗЯ, так как зажаты соседи (1,0) и (0,1).
        """
        grid_str = ".##G" # 0,0=free, 1,0=wall, 0,1=wall, 1,1=free
        planner = self.create_planner(grid_str, 2, 2)
        
        # Пытаемся пройти диагонально при 8-связности
        res = planner.find_path(0, 0, 1, 1, 
                                pfc.AlgorithmType.AStar, 
                                pfc.HeuristicType.Octile, 
                                1.0, 
                                8) # 8-связность
        
        self.assertFalse(res.found, "Срезание угла должно быть запрещено, если боковые клетки - стены")

    def test_diagonal_movement_allowed(self):
        """Проверка разрешенного диагонального хода (когда свободно вокруг)"""
        # . .
        # . G
        grid_str = ".... "
        planner = self.create_planner(grid_str, 2, 2)
        
        res = planner.find_path(0, 0, 1, 1, 
                                pfc.AlgorithmType.AStar, 
                                pfc.HeuristicType.Octile, 
                                1.0, 
                                8)
        
        self.assertTrue(res.found)
        # Длина должна быть sqrt(2) ≈ 1.414
        self.assertAlmostEqual(res.path_length, math.sqrt(2), places=3)

    def test_dijkstra_vs_astar_optimality(self):
        """Проверка, что A* (w=1) находит такой же оптимальный путь, как Dijkstra"""
        # Карта с препятствиями 5x5
        grid_str = (
            "....."
            ".###."
            "....."
            ".###."
            "....."
        )
        planner = self.create_planner(grid_str, 5, 5)
        
        start = (0, 0)
        goal = (4, 4)
        
        res_dijkstra = planner.find_path(start[0], start[1], goal[0], goal[1], 
                                         pfc.AlgorithmType.Dijkstra, pfc.HeuristicType.Zero, 1.0, 4)
        
        res_astar = planner.find_path(start[0], start[1], goal[0], goal[1], 
                                      pfc.AlgorithmType.AStar, pfc.HeuristicType.Manhattan, 1.0, 4)
        
        self.assertTrue(res_dijkstra.found)
        self.assertTrue(res_astar.found)
        
        # Длины путей должны совпадать (A* с допустимой эвристикой оптимален)
        self.assertAlmostEqual(res_dijkstra.path_length, res_astar.path_length, places=5)
        
        # Но A* должен раскрыть меньше (или столько же) вершин
        # (Это не строгая проверка для теста, но полезная для отладки)
        print(f"\nDijkstra exp: {res_dijkstra.expanded_nodes}, A* exp: {res_astar.expanded_nodes}")

if __name__ == '__main__':
    unittest.main()