import sys
import os

# --- 1. ПОДКЛЮЧЕНИЕ C++ ЯДРА ---
BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../build'))
sys.path.append(BUILD_DIR)

try:
    import pathfinding_core as pfc
except ImportError:
    print(f"❌ Ошибка: Не найден модуль 'pathfinding_core'")
    sys.exit(1)

# --- 2. ПУТИ К ДАННЫМ ---
TASK_NAME = "my"
BASE_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))

MAP_DIR = os.path.join(BASE_DATA_DIR, f'map/{TASK_NAME}')
SCEN_DIR = os.path.join(BASE_DATA_DIR, f'scen/{TASK_NAME}')

# --- 3. НАСТРОЙКИ СЕТКИ ---
# Выбор связности: 4 (только крестом) или 8 (с диагоналями)
CONNECTIVITY = 4

# --- 4. НАСТРОЙКИ СЦЕНАРИЕВ (SCENARIOS) ---
USE_SCENARIOS = True
TASKS_PER_SCENARIO = 300
SCENARIO_FILES = [
    "1.scen"
    # "maze_simple.map.scen"
    # "maze512-2-0.map.scen",
]

# --- 5. ВСЕ АЛГОРИТМЫ ДЛЯ БЕНЧМАРКА ---
BENCHMARK_ALGORITHMS = [
    ("BFS",            pfc.AlgorithmType.BFS,      pfc.HeuristicType.Zero,      1.0),
    ("Dijkstra",       pfc.AlgorithmType.Dijkstra, pfc.HeuristicType.Zero,      1.0),
    
    # A* с разными эвристиками
    ("A* (Manhattan)", pfc.AlgorithmType.AStar,    pfc.HeuristicType.Manhattan, 1.0),
    ("A* (Octile)",    pfc.AlgorithmType.AStar,    pfc.HeuristicType.Octile,    1.0),
    ("A* (Euclid)",    pfc.AlgorithmType.AStar,    pfc.HeuristicType.Euclidean, 1.0), 
    
    # WA* (Взвешенный A*) 
    ("WA* (x1.5)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    1.5),
    ("WA* (x2.0)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    2.0),
    ("WA* (x5.0)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    5.0),
]

# --- 6. НАСТРОЙКИ ДЛЯ ВИЗУАЛИЗАЦИИ ---
VISUAL_ALGOS = {
    "bfs":      (pfc.AlgorithmType.BFS,      pfc.HeuristicType.Zero,      1.0),
    "dijkstra": (pfc.AlgorithmType.Dijkstra, pfc.HeuristicType.Zero,      1.0),
    "astar":    (pfc.AlgorithmType.AStar,    pfc.HeuristicType.Octile,    1.0),
    "wastar":   (pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    1.5),
}