import sys
import os

# --- 1. ПУТИ И ЯДРО ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
BUILD_DIR = os.path.join(PROJECT_ROOT, 'build')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')

sys.path.append(BUILD_DIR)

try:
    import pathfinding_core as pfc
except ImportError:
    # print(f"❌ Warning: Не найден модуль 'pathfinding_core' в {BUILD_DIR}")
    pfc = None

# --- 2. ОБЩИЕ НАСТРОЙКИ ---
CONNECTIVITY = 8  # 4 или 8
MAP_TYPES = ['maze', 'random'] 

# --- 3. НАСТРОЙКИ ПО УМОЛЧАНИЮ (DEFAULTS) ---

# [VISUAL MODE]
DEFAULT_MAP_NAME = "maze/maze512-1-0.map"
DEFAULT_SCEN_NAME = "maze/maze512-1-0.map.scen"
DEFAULT_ALGO = "astar"
# Если ID = None, то визуализатор переходит в режим показа серии задач (LIMIT)
DEFAULT_VISUAL_ID = None  
# Сколько задач показывать подряд, если ID не задан
DEFAULT_VISUAL_LIMIT = 1  

DEFAULT_MAP = os.path.join(DATA_DIR, 'map', DEFAULT_MAP_NAME)
DEFAULT_SCEN = os.path.join(DATA_DIR, 'scen', DEFAULT_SCEN_NAME)

# [BENCH MODE]
BENCH_LIMIT = 10 # Лимит задач на сценарий

# [EXPERIMENTS MODE]
EXP_SAMPLING_MODE = 'all'  # 'all', 'uniform', 'first', 'last'
EXP_SAMPLING_COUNT = 20000
EXP_TARGET_MAP = "random512-30-0.map"       # Имя карты или None (все). ["maze512-1-0.map", "random512-40-0.map"]
EXPERIMENT_CONNECTIVITIES = [4, 8]            # [4, 8]. Для лабиринта лучше ставить 4

# --- 4. РЕЕСТР АЛГОРИТМОВ ---
if pfc:
    ALGO_REGISTRY = {
        "bfs":      (pfc.AlgorithmType.BFS,      pfc.HeuristicType.Zero,      1.0),
        "dijkstra": (pfc.AlgorithmType.Dijkstra, pfc.HeuristicType.Zero,      1.0),
        "astar":    (pfc.AlgorithmType.AStar,    pfc.HeuristicType.Octile,    1.0), 
        "manhattan":(pfc.AlgorithmType.AStar,    pfc.HeuristicType.Manhattan, 1.0),
        "euclid":   (pfc.AlgorithmType.AStar,    pfc.HeuristicType.Euclidean, 1.0),
        "wastar":   (pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    1.5),
    }
    
    # Список для массового тестирования
    EXPERIMENT_ALGORITHMS = [
        ("BFS",            pfc.AlgorithmType.BFS,      pfc.HeuristicType.Zero,      1.0),
        ("Dijkstra",       pfc.AlgorithmType.Dijkstra, pfc.HeuristicType.Zero,      1.0),
        ("A* (Octile)",    pfc.AlgorithmType.AStar,    pfc.HeuristicType.Octile,    1.0),
        ("WA* (x1.5)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    1.5),
        ("WA* (x2.0)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    2.0),
        ("WA* (x5.0)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    5.0),
        ("WA* (x10.0)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    10.0),

    ]
else:
    ALGO_REGISTRY = {}
    EXPERIMENT_ALGORITHMS = []