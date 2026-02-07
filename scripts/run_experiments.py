import sys
import os
import time

# Добавляем путь к build, чтобы импортировать pathfinding_core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../build')))

try:
    import pathfinding_core as pfc
except ImportError:
    print("❌ Не удалось найти модуль pathfinding_core. Убедитесь, что проект собран.")
    sys.exit(1)

from map_parser import MapParser
from visualizer import print_ascii_map

def main():
    # Путь к карте (замените на свой, если скачали другую)
    map_path = os.path.join(os.path.dirname(__file__), '../data/movingai/arena.map')
    
    # Проверка наличия файла
    if not os.path.exists(map_path):
        print(f"⚠️ Файл карты не найден: {map_path}")
        print("Скачайте карту с https://movingai.com/benchmarks/grids.html и положите в data/movingai/")
        return

    print(f"Загрузка карты: {map_path}")
    width, height, grid = MapParser.parse_map(map_path)
    print(f"Размер: {width}x{height}")

    planner = pfc.PathPlanner(width, height, grid)

    # Пример координат (для arena.map, если она пустая в центре)
    # Лучше брать координаты из .scen файла, но пока зададим вручную, чтобы просто проверить
    start = (5, 5)
    goal = (10, 10)

    print(f"\n--- Запуск экспериментов: {start} -> {goal} ---")

    experiments = [
        ("BFS", pfc.AlgorithmType.BFS, pfc.HeuristicType.Zero, 1.0),
        ("Dijkstra", pfc.AlgorithmType.Dijkstra, pfc.HeuristicType.Zero, 1.0),
        ("A* (Manhattan)", pfc.AlgorithmType.AStar, pfc.HeuristicType.Manhattan, 1.0),
        ("A* (Octile)", pfc.AlgorithmType.AStar, pfc.HeuristicType.Octile, 1.0),
        ("WA* (w=1.5)", pfc.AlgorithmType.WAStar, pfc.HeuristicType.Octile, 1.5),
    ]

    print(f"{'Algorithm':<20} | {'Found':<5} | {'Len':<10} | {'Nodes':<8} | {'Time (s)':<10}")
    print("-" * 70)

    for name, algo, heur, weight in experiments:
        # Тестируем на 8-связном графе (стандарт для игр)
        res = planner.find_path(
            start[0], start[1], goal[0], goal[1],
            algo, heur, weight, 8
        )

        # Печатаем результат
        # found_str = "Yes" if res.found else "No"
        # print(f"{name:<20} | {found_str:<5} | {res.path_length:<10.4f} | ...")
        
        # ДОБАВИТЬ ЭТОТ БЛОК:
        if res.found:
            print(f"Визуализация пути для {name}:")
            # Преобразуем список пар координат C++ в список Python
            path_list = res.path 
            print_ascii_map(width, height, grid, path_list, start, goal)
            print("\n")
        
        found_str = "Yes" if res.found else "No"
        print(f"{name:<20} | {found_str:<5} | {res.path_length:<10.4f} | {res.expanded_nodes:<8} | {res.execution_time:<10.6f}")

if __name__ == "__main__":
    main()