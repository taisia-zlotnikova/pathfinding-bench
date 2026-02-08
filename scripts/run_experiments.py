import os
import sys
import csv
import time
from datetime import datetime

# --- Настройка путей (аналогично config.py) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
BUILD_DIR = os.path.join(PROJECT_ROOT, 'build')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')

sys.path.append(BUILD_DIR)

# Пытаемся импортировать C++ модуль и парсер
try:
    import pathfinding_core as pfc
    from map_parser import MapParser
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print(f"Убедитесь, что .so файл находится в {BUILD_DIR}")
    sys.exit(1)

# --- Конфигурация экспериментов ---
# Типы карт (названия папок в data/map)
MAP_TYPES = ['maze', 'random', 'my']  # Можно добавить другие, если есть
# Типы связности
CONNECTIVITIES = [4, 8]

# Список алгоритмов для тестирования: (Display Name, AlgoEnum, HeurEnum, Weight)
ALGORITHMS = [
    ("BFS",            pfc.AlgorithmType.BFS,      pfc.HeuristicType.Zero,      1.0),
    ("Dijkstra",       pfc.AlgorithmType.Dijkstra, pfc.HeuristicType.Zero,      1.0),
    ("A* (Manhattan)", pfc.AlgorithmType.AStar,    pfc.HeuristicType.Manhattan, 1.0),
    ("A* (Euclid)",    pfc.AlgorithmType.AStar,    pfc.HeuristicType.Euclidean, 1.0),
    ("A* (Octile)",    pfc.AlgorithmType.AStar,    pfc.HeuristicType.Octile,    1.0),
    ("WA* (x1.5)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    1.5),
    ("WA* (x2.0)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    2.0),
    # ("WA* (x5.0)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    5.0), # Опционально
]

def ensure_dirs():
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

def run_all_experiments():
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = os.path.join(RESULTS_DIR, f"results_{timestamp}.csv")
    
    # Заголовки CSV
    headers = [
        "MapType", "MapName", "Scenario", "Connectivity", 
        "Algorithm", "Weight", "TaskID", 
        "Success", "PathLength", "OptimalLength", 
        "ExpandedNodes", "TimeMS", "Suboptimality"
    ]

    print(f"🚀 Запуск полного тестирования...")
    print(f"📂 Результаты будут записаны в: {csv_file}")

    with open(csv_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        # 1. Перебор типов карт (maze, random, my)
        for map_type in MAP_TYPES:
            scen_dir = os.path.join(DATA_DIR, 'scen', map_type)
            map_dir = os.path.join(DATA_DIR, 'map', map_type)

            if not os.path.exists(scen_dir):
                print(f"⚠️ Папка сценариев не найдена: {scen_dir}, пропускаем.")
                continue

            # Получаем список файлов сценариев
            scen_files = [f for f in os.listdir(scen_dir) if f.endswith('.scen')]
            
            for scen_file in scen_files:
                scen_path = os.path.join(scen_dir, scen_file)
                
                # Парсим сценарий
                try:
                    tasks = MapParser.parse_scenarios(scen_path)
                except Exception as e:
                    print(f"❌ Ошибка парсинга сценария {scen_file}: {e}")
                    continue

                if not tasks:
                    continue

                # Определяем имя карты из первого задания сценария
                map_name = tasks[0]["map_name"]
                map_path = os.path.join(map_dir, map_name)

                if not os.path.exists(map_path):
                    # Попытка найти карту, если путь в сценарии относительный или некорректный
                    print(f"⚠️ Карта {map_name} не найдена в {map_dir}. Пропуск.")
                    continue

                print(f"   🗺️  Карта: {map_name} | Сценарий: {scen_file}")

                # Загружаем карту (один раз для всех задач в файле)
                try:
                    width, height, grid = MapParser.parse_map(map_path)
                    planner = pfc.PathPlanner(width, height, grid)
                except Exception as e:
                    print(f"❌ Ошибка загрузки карты {map_name}: {e}")
                    continue

                # 2. Перебор связности (4 и 8)
                for connectivity in CONNECTIVITIES:
                    # 3. Перебор алгоритмов
                    for algo_name, algo_enum, heur_enum, weight in ALGORITHMS:
                        
                        # Запускаем задачи (ограничим 100 задачами на файл для скорости, если их много)
                        limit_tasks = 50 
                        current_tasks = tasks[:limit_tasks]

                        for task in current_tasks:
                            start = task["start"]
                            goal = task["goal"]
                            optimal_len = task["optimal_len"]

                            # ЗАПУСК C++ ЯДРА
                            res = planner.find_path(
                                start[0], start[1], 
                                goal[0], goal[1], 
                                algo_enum, heur_enum, weight, 
                                connectivity
                            )
                            
                            # Расчет субоптимальности (насколько путь длиннее эталона)
                            # OptimalLength может быть 0, если точки совпадают
                            subopt = 0.0
                            if res.found and optimal_len > 0:
                                subopt = (res.path_length - optimal_len) / optimal_len * 100
                            elif res.found and optimal_len == 0:
                                subopt = 0.0
                            
                            # Запись строки результата
                            writer.writerow([
                                map_type, map_name, scen_file, connectivity,
                                algo_name, weight, task["id"],
                                res.found, 
                                f"{res.path_length:.4f}", 
                                optimal_len,
                                res.expanded_nodes, 
                                f"{res.execution_time * 1000:.4f}", # ms
                                f"{subopt:.2f}" # %
                            ])
                        
                        # Чтобы видеть прогресс, флуш буфера не делаем каждый раз, но принт можно
                        # print(f"      ✅ {algo_name} (Conn: {connectivity}) завершен.")

    print(f"\n🏁 Тестирование завершено! Файл сохранен: {csv_file}")

if __name__ == "__main__":
    run_all_experiments()