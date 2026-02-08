import os
import sys
import csv
import random
from datetime import datetime

# --- 1. НАСТРОЙКИ ТЕСТИРОВАНИЯ ---
# Режим выборки задач:
#   'all'     - Все задачи из сценария (для глубокого анализа одной карты)
#   'uniform' - Равномерная выборка (например, 100 задач разной сложности)
#   'first'   - Выборка первых N задач
#   'last'    - Выборка последних N задач
SAMPLING_MODE = 'first'  
SAMPLING_COUNT = 100   # Используется только если mode != 'all'

# --- 2. ФИЛЬТР ПО ОДНОЙ КАРТЕ ---
# Если хотите протестировать ТОЛЬКО одну карту, укажите имя файла.
# Пример: "maze512-1-0.map"
# Если None - тестируются все карты подряд.
TARGET_MAP_NAME = None 
# TARGET_MAP_NAME = "maze512-1-1.map"
# TARGET_MAP_NAME = "random512-10-2.map"

# --- Настройка путей ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
BUILD_DIR = os.path.join(PROJECT_ROOT, 'build')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')

sys.path.append(BUILD_DIR)

try:
    import pathfinding_core as pfc
    from map_parser import MapParser
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

# --- Алгоритмы ---
MAP_TYPES = ['maze', 'random', 'my']
CONNECTIVITIES = [4, 8]

ALGORITHMS = [
    ("BFS",            pfc.AlgorithmType.BFS,      pfc.HeuristicType.Zero,      1.0),
    ("Dijkstra",       pfc.AlgorithmType.Dijkstra, pfc.HeuristicType.Zero,      1.0),
    ("A* (Manhattan)", pfc.AlgorithmType.AStar,    pfc.HeuristicType.Manhattan, 1.0),
    ("A* (Euclid)",    pfc.AlgorithmType.AStar,    pfc.HeuristicType.Euclidean, 1.0),
    ("A* (Octile)",    pfc.AlgorithmType.AStar,    pfc.HeuristicType.Octile,    1.0),
    ("WA* (x1.5)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    1.5),
    ("WA* (x2.0)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    2.0),
]

def get_tasks_subset(tasks, mode, count):
    total = len(tasks)
    if mode == 'all' or total <= count:
        return tasks, "All"
    if mode == 'first':
        return tasks[:count], f"First {count}"
    elif mode == 'last':
        return tasks[-count:], f"Last {count}"
    elif mode == 'uniform':
        step = total / count
        indices = sorted(list(set([int(i * step) for i in range(count)])))
        return [tasks[i] for i in indices], f"Uniform {len(indices)}"
    elif mode == 'random':
        random.seed(42)
        return random.sample(tasks, count), f"Random {count}"
    return tasks, "Unknown"

def run_experiments():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Формируем имя папки
    if TARGET_MAP_NAME:
        subfolder_name = "single_map_tests"
    else:
        subfolder_name = "all_tasks" if SAMPLING_MODE == 'all' else f"{SAMPLING_MODE}_{SAMPLING_COUNT}"

    print(f"🎯 Режим: {SAMPLING_MODE.upper()} | Карта: {TARGET_MAP_NAME if TARGET_MAP_NAME else 'ВСЕ'}")

    for map_type in MAP_TYPES:
        scen_source_dir = os.path.join(DATA_DIR, 'scen', map_type)
        map_source_dir = os.path.join(DATA_DIR, 'map', map_type)
        
        if not os.path.exists(scen_source_dir): continue

        # 1. Сначала ищем подходящие сценарии
        valid_scenarios = []
        scen_files = [f for f in os.listdir(scen_source_dir) if f.endswith('.scen')]
        
        print(f"\n🔍 Сканирование папки {map_type} ({len(scen_files)} файлов)...")
        
        for scen_file in scen_files:
            full_path = os.path.join(scen_source_dir, scen_file)
            try:
                tasks = MapParser.parse_scenarios(full_path)
                if not tasks: continue
                
                map_name = tasks[0]["map_name"]
                
                # ГЛАВНЫЙ ФИЛЬТР
                if TARGET_MAP_NAME and map_name != TARGET_MAP_NAME:
                    continue
                
                # Проверяем наличие самой карты
                if not os.path.exists(os.path.join(map_source_dir, map_name)):
                    # print(f"   ⚠️ Карта {map_name} не найдена.") # Можно раскомментировать для отладки
                    continue
                    
                valid_scenarios.append((scen_file, map_name, tasks))
                
            except Exception:
                continue

        if not valid_scenarios:
            if TARGET_MAP_NAME:
                print(f"   ℹ️ В папке {map_type} нет сценариев для карты {TARGET_MAP_NAME}")
            continue
        
        # Сортируем сценарии по имени карты, чтобы группировать загрузку
        # Это критично для эффективности кэширования
        valid_scenarios.sort(key=lambda x: x[1])

        # 2. Создаем CSV
        current_result_dir = os.path.join(RESULTS_DIR, map_type, subfolder_name)
        os.makedirs(current_result_dir, exist_ok=True)
        
        name_part = f"_{TARGET_MAP_NAME}" if TARGET_MAP_NAME else ""
        csv_filename = f"res_{map_type}{name_part}_{timestamp}.csv"
        csv_path = os.path.join(current_result_dir, csv_filename)

        print(f"🚀 Запуск тестов для {len(valid_scenarios)} сценариев. Файл: {csv_filename}")

        # --- ПЕРЕМЕННЫЕ ДЛЯ КЭШИРОВАНИЯ ---
        cached_map_name = None
        cached_planner = None

        with open(csv_path, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["MapName", "Scenario", "Connectivity", "Algorithm", "Weight", 
                             "TaskID", "Success", "PathLength", "OptimalLength", 
                             "ExpandedNodes", "TimeMS", "Suboptimality"])

            for scen_file, map_name, all_tasks in valid_scenarios:
                
                # --- ЛОГИКА КЭШИРОВАНИЯ ---
                if map_name != cached_map_name:
                    # Если карта изменилась, загружаем новую
                    try:
                        # print(f"   💾 Загрузка карты: {map_name}...") # Раскомментируйте, если хотите видеть момент загрузки
                        width, height, grid = MapParser.parse_map(os.path.join(map_source_dir, map_name))
                        planner = pfc.PathPlanner(width, height, grid)
                        
                        # Обновляем кэш
                        cached_map_name = map_name
                        cached_planner = planner
                    except Exception as e:
                        print(f"❌ Ошибка загрузки карты {map_name}: {e}")
                        cached_map_name = None
                        cached_planner = None
                        continue
                else:
                    # Если карта та же самая, используем кэш
                    planner = cached_planner
                    # print(f"   ⚡ Cache hit: {map_name}") 
                
                if not planner: continue

                # Выборка задач
                current_tasks, desc = get_tasks_subset(all_tasks, SAMPLING_MODE, SAMPLING_COUNT)
                print(f"   🗺️  {map_name} | {scen_file[:20]:<20} | {desc} (Tasks: {len(all_tasks)})")

                for conn in CONNECTIVITIES:
                    for algo_name, algo_enum, heur_enum, weight in ALGORITHMS:
                        for task in current_tasks:
                            res = planner.find_path(
                                task["start"][0], task["start"][1], 
                                task["goal"][0], task["goal"][1], 
                                algo_enum, heur_enum, weight, conn
                            )

                            subopt = 0.0
                            if res.found and task["optimal_len"] > 0:
                                subopt = (res.path_length - task["optimal_len"]) / task["optimal_len"] * 100
                            
                            writer.writerow([
                                map_name, scen_file, conn, algo_name, weight, task["id"],
                                res.found, f"{res.path_length:.4f}", task["optimal_len"],
                                res.expanded_nodes, f"{res.execution_time * 1000:.4f}", f"{subopt:.2f}"
                            ])
        print("✅ Готово.")

if __name__ == "__main__":
    run_experiments()