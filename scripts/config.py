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
    print(f"❌ Warning: Не найден модуль 'pathfinding_core' в {BUILD_DIR}")
    pfc = None

# --- 2. ОБЩИЕ НАСТРОЙКИ ---
CONNECTIVITY = 8  # 4 или 8
MAP_TYPES = ['maze',
             'random',
             'my', 
                ] # Папки, которые сканируем в data/map

# --- 3. НАСТРОЙКИ ПО УМОЛЧАНИЮ (DEFAULTS) ---
# Для режима Visual
DEFAULT_MAP = "maze/maze512-1-0.map"
DEFAULT_SCEN = "maze/maze512-1-0.map.scen"
DEFAULT_ALGO = "astar"

# Для режима Bench
BENCH_LIMIT = 10 # Лимит задач на сценарий

# Для режима Experiments
EXP_SAMPLING_MODE = 'first'  # 'all', 'uniform', 'first', 'last'
EXP_SAMPLING_COUNT = 10
EXP_TARGET_MAP = None          # Имя карты (напр. "random512.map") или None (все)

# --- 4. РЕЕСТР АЛГОРИТМОВ ---

# Словарь для CLI (строка -> параметры)
if pfc:
    ALGO_REGISTRY = {
        "bfs":      (pfc.AlgorithmType.BFS,      pfc.HeuristicType.Zero,      1.0),
        "dijkstra": (pfc.AlgorithmType.Dijkstra, pfc.HeuristicType.Zero,      1.0),
        "astar":    (pfc.AlgorithmType.AStar,    pfc.HeuristicType.Octile,    1.0), 
        "manhattan":(pfc.AlgorithmType.AStar,    pfc.HeuristicType.Manhattan, 1.0),
        "euclid":   (pfc.AlgorithmType.AStar,    pfc.HeuristicType.Euclidean, 1.0),
        "wastar":   (pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    1.5),
    }

    # Список для массового тестирования (Experiments)
    EXPERIMENT_ALGORITHMS = [
        ("BFS",            pfc.AlgorithmType.BFS,      pfc.HeuristicType.Zero,      1.0),
        ("Dijkstra",       pfc.AlgorithmType.Dijkstra, pfc.HeuristicType.Zero,      1.0),
        ("A* (Octile)",    pfc.AlgorithmType.AStar,    pfc.HeuristicType.Octile,    1.0),
        ("WA* (x1.5)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    1.5),
        ("WA* (x2.0)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    2.0),
        # ("WA* (x5.0)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    5.0),
    ]
else:
    ALGO_REGISTRY = {}
    EXPERIMENT_ALGORITHMS = []