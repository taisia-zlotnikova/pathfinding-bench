import os
import sys
import csv
import time
from datetime import datetime

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
    print(f"Убедитесь, что .so файл находится в {BUILD_DIR}")
    sys.exit(1)

# --- Конфигурация ---
# Типы карт для тестирования (совпадают с именами папок в data/map)
MAP_TYPES = ['maze', 'random', 'my']
CONNECTIVITIES = [4, 8]

# (Название, AlgoEnum, HeurEnum, Вес)
ALGORITHMS = [
    ("BFS",            pfc.AlgorithmType.BFS,      pfc.HeuristicType.Zero,      1.0),
    ("Dijkstra",       pfc.AlgorithmType.Dijkstra, pfc.HeuristicType.Zero,      1.0),
    ("A* (Manhattan)", pfc.AlgorithmType.AStar,    pfc.HeuristicType.Manhattan, 1.0),
    ("A* (Euclid)",    pfc.AlgorithmType.AStar,    pfc.HeuristicType.Euclidean, 1.0),
    ("A* (Octile)",    pfc.AlgorithmType.AStar,    pfc.HeuristicType.Octile,    1.0),
    ("WA* (x1.5)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    1.5),
    ("WA* (x2.0)",     pfc.AlgorithmType.WAStar,   pfc.HeuristicType.Octile,    2.0),
]

def run_experiments():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Итерируемся по типам карт (maze, random, etc.)
    for map_type in MAP_TYPES:
        print(f"\n🚀 --- ЗАПУСК ТЕСТОВ ДЛЯ ТИПА: {map_type.upper()} ---")
        
        # 1. Подготовка путей
        scen_source_dir = os.path.join(DATA_DIR, 'scen', map_type)
        map_source_dir = os.path.join(DATA_DIR, 'map', map_type)
        
        # Папка для результатов именно этого типа
        current_result_dir = os.path.join(RESULTS_DIR, map_type)
        os.makedirs(current_result_dir, exist_ok=True)
        
        csv_path = os.path.join(current_result_dir, f"results_{map_type}_{timestamp}.csv")

        if not os.path.exists(scen_source_dir):
            print(f"⚠️ Папка сценариев не найдена: {scen_source_dir}. Пропуск.")
            continue

        # 2. Открываем CSV для записи
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
                    tasks = MapParser.parse_scenarios(scen_full_path)
                except Exception as e:
                    print(f"❌ Ошибка сценария {scen_file}: {e}")
                    continue
                
                if not tasks: continue

                # Загружаем карту
                map_name = tasks[0]["map_name"]
                map_path = os.path.join(map_source_dir, map_name)
                
                if not os.path.exists(map_path):
                    print(f"⚠️ Карта {map_name} не найдена. Пропуск.")
                    continue

                print(f"   🗺️  Карта: {map_name} | Задач: {len(tasks)}")
                
                try:
                    width, height, grid = MapParser.parse_map(map_path)
                    planner = pfc.PathPlanner(width, height, grid)
                except Exception as e:
                    print(f"❌ Ошибка карты: {e}")
                    continue

                # Ограничиваем кол-во задач для скорости (например, 50)
                limit_tasks = 50
                current_tasks = tasks[:limit_tasks]

                for conn in CONNECTIVITIES:
                    for algo_name, algo_enum, heur_enum, weight in ALGORITHMS:
                        
                        for task in current_tasks:
                            res = planner.find_path(
                                task["start"][0], task["start"][1], 
                                task["goal"][0], task["goal"][1], 
                                algo_enum, heur_enum, weight, conn
                            )

                            # Считаем субоптимальность
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
        
        print(f"✅ Результаты сохранены в: {csv_path}")

if __name__ == "__main__":
    run_experiments()