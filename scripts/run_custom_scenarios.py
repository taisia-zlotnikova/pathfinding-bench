import sys
import os

# 1. Настройка путей (чтобы Python видел C++ модуль и визуализатор)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../build')))
try:
    import pathfinding_core as pfc
except ImportError:
    print("❌ Ошибка: Не найден модуль pathfinding_core. Соберите проект (make).")
    sys.exit(1)

# Импортируем функцию рисования
try:
    from visualizer import print_ascii_map
except ImportError:
    # Если вдруг файла нет, определим заглушку, чтобы скрипт не падал
    def print_ascii_map(*args): print("Visualizer not found")

def run_visual_test(map_str, name="Test", algo=pfc.AlgorithmType.AStar, heuristic=pfc.HeuristicType.Manhattan):
    """
    Парсит строковую карту, запускает поиск и рисует результат.
    Легенда карты:
    S - Старт
    G - Финиш
    # или @ - Стена
    . - Пусто
    """
    lines = [line.strip() for line in map_str.strip().split('\n')]
    height = len(lines)
    width = len(lines[0])
    
    grid = []
    start = (0, 0)
    goal = (0, 0)
    
    # Парсим карту из строк в список чисел
    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            if char == 'S':
                start = (x, y)
                grid.append(0)
            elif char == 'G':
                goal = (x, y)
                grid.append(0)
            elif char in ['#', '@', 'T']:
                grid.append(1) # Препятствие
            else:
                grid.append(0) # Пусто
                
    # Создаем планировщик
    planner = pfc.PathPlanner(width, height, grid)
    
    # Запускаем поиск
    print(f"\n=== Сценарий: {name} ===")
    print(f"Карта {width}x{height}, Алгоритм: {algo}, Старт: {start}, Цель: {goal}")
    
    res = planner.find_path(
        start[0], start[1], goal[0], goal[1],
        algo, heuristic, 1.0, 8 # 8-связность
    )
    
    if res.found:
        print(f"✅ Путь найден! Длина: {res.path_length:.2f}, Вершин раскрыто: {res.expanded_nodes}")
        print_ascii_map(width, height, grid, res.path, start, goal)
    else:
        print("❌ Путь НЕ найден!")
        print_ascii_map(width, height, grid, [], start, goal)

if __name__ == "__main__":
    # --- ВАШИ ТЕСТЫ ПИШИТЕ ЗДЕСЬ ---
    
    # Тест 1: Простой обход стены
    map1 = """
    S...
    .##.
    .G#.
    ....
    """
    run_visual_test(map1, "Обход стены")

    # Тест 2: Лабиринт (проверка A*)
    map2 = """
    S.#...
    .##.#.
    ....#.
    .####.
    ....G.
    """
    run_visual_test(map2, "Лабиринт", pfc.AlgorithmType.AStar)

    # Тест 3: Ловушка (пути нет)
    map3 = """
    S....
    #####
    ....G
    """
    run_visual_test(map3, "Ловушка (нет пути)", pfc.AlgorithmType.BFS)
    
    # Тест 4: Узкий проход (проверка corner cutting)
    # Если алгоритм попытается срезать угол между (1,0) и (0,1), он врежется
    map4 = """
    .##.
    S..#
    #..G
    .##.
    """
    run_visual_test(map4, "Узкий диагональный проход", pfc.AlgorithmType.AStar, pfc.HeuristicType.Octile)