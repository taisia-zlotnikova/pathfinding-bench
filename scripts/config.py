import sys
import os

# --- 1. ПОДКЛЮЧЕНИЕ C++ ЯДРА ---
# Добавляем путь к папке build, чтобы Python видел библиотеку
BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../build'))
sys.path.append(BUILD_DIR)

try:
    import pathfinding_core as pfc
except ImportError:
    print(f"❌ Ошибка: Не найден модуль 'pathfinding_core' в папке {BUILD_DIR}")
    print("   Сначала соберите проект (команда make в папке build).")
    sys.exit(1)

# --- 2. ПУТИ К ДАННЫМ ---
TASK_NAME = "maze"

BASE_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
MAP_DIR = os.path.join(BASE_DATA_DIR, f'map/{TASK_NAME}')
SCEN_DIR = os.path.join(BASE_DATA_DIR, f'scen/{TASK_NAME}')

# --- 5. НАСТРОЙКИ СЦЕНАРИЕВ (SCENARIOS) ---
# Если True, бенчмарк будет брать задачи из файлов .scen
# Если False, будет генерировать случайные точки Start/Goal
USE_SCENARIOS = True
TASKS_PER_SCENARIO = 300

# Теперь указываем только ИМЯ файла сценария
SCENARIO_FILES = [
    "maze512-2-0.map.scen"
    # "maze_simple.map.scen"
]

# --- 3. НАСТРОЙКИ ДЛЯ БЕНЧМАРКА (BENCHMARK) ---
# Список алгоритмов, которые будут запускаться при режиме 'bench'
# Формат: ("Название", Алгоритм, Эвристика, Вес)
BENCHMARK_ALGORITHMS = [
    # Классические алгоритмы
    # ("BFS",            pfc.AlgorithmType.BFS,      pfc.HeuristicType.Zero,      1.0),
    ("Dijkstra",       pfc.AlgorithmType.Dijkstra, pfc.HeuristicType.Zero,      1.0),
    
    # # A* с разными эвристиками
    # ("A* (Manhattan)", pfc.AlgorithmType.AStar,    pfc.HeuristicType.Manhattan, 1.0),
    # ("A* (Octile)",    pfc.AlgorithmType.AStar,    pfc.HeuristicType.Octile,    1.0),
    # ("A* (Euclid)",    pfc.AlgorithmType.AStar,    pfc.HeuristicType.Euclidean, 1.0), 
    
    # WA* (Взвешенный A*) - поиск быстрее, но путь может быть не идеальным
    # Чем больше вес, тем быстрее работает, но хуже путь
    # ("WA* (x1.2)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    1.2),
    # ("WA* (x1.5)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    1.5),
    # ("WA* (x2.0)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    2.0),
    ("WA* (x5.0)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    5.0),
]

# --- 4. НАСТРОЙКИ ДЛЯ ВИЗУАЛИЗАЦИИ (VISUAL) ---
# Словарь алгоритмов, доступных через флаг --algo
# Пример запуска: python main.py visual --map ... --algo bfs
VISUAL_ALGOS = {
    "bfs":      (pfc.AlgorithmType.BFS,      pfc.HeuristicType.Zero,      1.0),
    "dijkstra": (pfc.AlgorithmType.Dijkstra, pfc.HeuristicType.Zero,      1.0),
    "astar":    (pfc.AlgorithmType.AStar,    pfc.HeuristicType.Octile,    1.0),
    "wastar":   (pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    1.5), # WA* с весом 1.5
    "greedy":   (pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    10.0) # Очень жадный поиск
}