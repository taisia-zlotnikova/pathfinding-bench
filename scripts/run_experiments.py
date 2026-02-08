import os
import sys
import csv
import random
from datetime import datetime

# --- 1. НАСТРОЙКИ ВЫБОРКИ (SAMPLING) ---
# Доступные режимы:
#   'all'     - Все задачи (осторожно, может быть долго!)
#   'first'   - Первые N задач (обычно самые легкие/короткие)
#   'last'    - Последние N задач (обычно самые сложные)
#   'uniform' - N задач, равномерно распределенных по всему файлу
#   'random'  - N случайных задач

SAMPLING_MODE = 'first'  
SAMPLING_COUNT = 100       # Количество задач (игнорируется, если mode='all')

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

# --- Конфигурация алгоритмов ---
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
    """Возвращает подмножество задач в зависимости от режима"""
    total = len(tasks)
    if mode == 'all' or total <= count:
        return tasks, "All"
    
    if mode == 'first':
        return tasks[:count], f"First {count}"
    
    elif mode == 'last':
        return tasks[-count:], f"Last {count}"
    
    elif mode == 'uniform':
        step = total / count
        indices = [int(i * step) for i in range(count)]
        # Убираем дубликаты индексов, если шаг < 1
        indices = sorted(list(set(indices)))
        return [tasks[i] for i in indices], f"Uniform {len(indices)}"
    
    elif mode == 'random':
        random.seed(42) # Фиксируем seed для воспроизводимости
        return random.sample(tasks, count), f"Random {count}"
    
    return tasks, "Unknown"

def run_experiments():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Формируем имя подпапки на основе режима: "uniform_100" или "all"
    if SAMPLING_MODE == 'all':
        subfolder_name = "all_tasks"
    else:
        subfolder_name = f"{SAMPLING_MODE}_{SAMPLING_COUNT}"

    print(f"🎯 Режим тестирования: {SAMPLING_MODE.upper()} (Count: {SAMPLING_COUNT})")
    print(f"📂 Результаты будут в подпапках: .../{subfolder_name}/")

    for map_type in MAP_TYPES:
        print(f"\n🚀 --- ТИП КАРТЫ: {map_type.upper()} ---")
        
        scen_source_dir = os.path.join(DATA_DIR, 'scen', map_type)
        map_source_dir = os.path.join(DATA_DIR, 'map', map_type)
        
        # Создаем папку: results/maze/uniform_100/
        current_result_dir = os.path.join(RESULTS_DIR, map_type, subfolder_name)
        os.makedirs(current_result_dir, exist_ok=True)
        
        csv_filename = f"res_{map_type}_{subfolder_name}_{timestamp}.csv"
        csv_path = os.path.join(current_result_dir, csv_filename)

        if not os.path.exists(scen_source_dir):
            print(f"⚠️ Папка {scen_source_dir} не найдена. Пропуск.")
            continue

        with open(csv_path, mode='w', newline='') as f:
            writer = csv.writer(f)
            headers = [
                "MapName", "Scenario", "Connectivity", 
                "Algorithm", "Weight", "TaskID", 
                "Success", "PathLength", "OptimalLength", 
                "ExpandedNodes", "TimeMS", "Suboptimality"
            ]
            writer.writerow(headers)

            scen_files = [f for f in os.listdir(scen_source_dir) if f.endswith('.scen')]
            
            for scen_file in scen_files:
                scen_full_path = os.path.join(scen_source_dir, scen_file)
                try:
                    all_tasks = MapParser.parse_scenarios(scen_full_path)
                except Exception as e:
                    print(f"❌ Ошибка сценария {scen_file}: {e}")
                    continue
                
                if not all_tasks: continue

                map_name = all_tasks[0]["map_name"]
                map_path = os.path.join(map_source_dir, map_name)
                
                if not os.path.exists(map_path):
                    print(f"⚠️ Карта {map_name} не найдена. Пропуск.")
                    continue

                try:
                    width, height, grid = MapParser.parse_map(map_path)
                    planner = pfc.PathPlanner(width, height, grid)
                except Exception as e:
                    print(f"❌ Ошибка карты: {e}")
                    continue

                # --- ПРИМЕНЯЕМ ВЫБОРКУ ---
                current_tasks, desc = get_tasks_subset(all_tasks, SAMPLING_MODE, SAMPLING_COUNT)
                print(f"   🗺️  {map_name[:20]:<20} | {desc} (из {len(all_tasks)})")

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
                                map_name, scen_file, conn,
                                algo_name, weight, task["id"],
                                res.found, 
                                f"{res.path_length:.4f}", 
                                task["optimal_len"],
                                res.expanded_nodes, 
                                f"{res.execution_time * 1000:.4f}",
                                f"{subopt:.2f}"
                            ])
        
        print(f"✅ Сохранено: {csv_path}")

if __name__ == "__main__":
    run_experiments()