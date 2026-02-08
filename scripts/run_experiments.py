import os
import sys
import csv
import random
from datetime import datetime
import config

try:
    import pathfinding_core as pfc
    from map_parser import MapParser
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

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

def run_experiments_logic(sampling_mode=None, sampling_count=None, target_map=None):
    # Применяем каскад настроек: Аргумент -> Конфиг
    mode = sampling_mode if sampling_mode else config.EXP_SAMPLING_MODE
    count = sampling_count if sampling_count else config.EXP_SAMPLING_COUNT
    target_map = target_map if target_map else config.EXP_TARGET_MAP

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Имя подпапки
    if target_map:
        subfolder_name = "single_map_tests"
    else:
        subfolder_name = "all_tasks" if mode == 'all' else f"{mode}_{count}"

    print(f"🎯 EXPERIMENTS STARTED")
    print(f"   Mode: {mode.upper()} | Count: {count} | Map: {target_map if target_map else 'ALL'}")

    for map_type in config.MAP_TYPES:
        scen_source_dir = os.path.join(config.DATA_DIR, 'scen', map_type)
        map_source_dir = os.path.join(config.DATA_DIR, 'map', map_type)
        
        if not os.path.exists(scen_source_dir): continue

        # 1. Сбор сценариев
        valid_scenarios = []
        try:
            scen_files = [f for f in os.listdir(scen_source_dir) if f.endswith('.scen')]
        except FileNotFoundError:
            continue
        
        if not scen_files: continue
        
        print(f"\n🔍 Scanning {map_type} ({len(scen_files)} files)...")
        
        for scen_file in scen_files:
            full_path = os.path.join(scen_source_dir, scen_file)
            try:
                tasks = MapParser.parse_scenarios(full_path)
                if not tasks: continue
                
                map_name = tasks[0]["map_name"]
                
                # Фильтр по карте
                if target_map and map_name != target_map:
                    continue
                
                # Проверка наличия файла карты
                if not os.path.exists(os.path.join(map_source_dir, map_name)):
                    continue
                    
                valid_scenarios.append((scen_file, map_name, tasks))
            except Exception:
                continue

        if not valid_scenarios:
            if target_map:
                print(f"   ℹ️ Skip {map_type}: No scenarios for {target_map}")
            continue
        
        # Сортировка для кэширования
        valid_scenarios.sort(key=lambda x: x[1])

        # 2. Подготовка CSV
        current_result_dir = os.path.join(config.RESULTS_DIR, map_type, subfolder_name)
        os.makedirs(current_result_dir, exist_ok=True)
        
        name_part = f"_{target_map}" if target_map else ""
        csv_filename = f"res_{map_type}{name_part}_{timestamp}.csv"
        csv_path = os.path.join(current_result_dir, csv_filename)

        print(f"🚀 Running tests for {len(valid_scenarios)} scenarios -> {csv_filename}")

        cached_map_name = None
        cached_planner = None

        with open(csv_path, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["MapName", "Scenario", "Connectivity", "Algorithm", "Weight", 
                             "TaskID", "Success", "PathLength", "OptimalLength", 
                             "ExpandedNodes", "TimeMS", "Suboptimality"])

            for scen_file, map_name, all_tasks in valid_scenarios:
                
                # Кэширование карты
                if map_name != cached_map_name:
                    try:
                        width, height, grid = MapParser.parse_map(os.path.join(map_source_dir, map_name))
                        planner = pfc.PathPlanner(width, height, grid)
                        cached_map_name = map_name
                        cached_planner = planner
                    except Exception as e:
                        print(f"❌ Error loading {map_name}: {e}")
                        cached_map_name = None
                        cached_planner = None
                        continue
                else:
                    planner = cached_planner
                
                if not planner: continue

                # Выборка задач
                current_tasks, desc = get_tasks_subset(all_tasks, mode, count)
                print(f"   🗺️  {map_name} | {scen_file[:20]:<20} | {desc}")

                # Запуск алгоритмов
                # Используем алгоритмы из config.py
                connectivities = [4, 8] # Можно вынести в конфиг, но обычно тестируем оба
                
                for conn in connectivities:
                    for algo_name, algo_enum, heur_enum, weight in config.EXPERIMENT_ALGORITHMS:
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
        print("✅ Done.")

if __name__ == "__main__":
    # Если запущен напрямую, используем дефолтные настройки
    run_experiments_logic()