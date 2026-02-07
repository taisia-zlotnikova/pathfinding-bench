import os
import random
import argparse
import config  
import pathfinding_core as pfc # Теперь pfc доступен, так как config настроил sys.path

from map_parser import MapParser

# Пытаемся импортировать визуализатор
try:
    from visualizer import print_ascii_map
except ImportError:
    print_ascii_map = None

def get_random_valid_points(width, height, grid, min_dist=1):
    """Ищет две случайные свободные точки на карте."""
    max_attempts = 1000
    for _ in range(max_attempts):
        x1, y1 = random.randint(0, width-1), random.randint(0, height-1)
        x2, y2 = random.randint(0, width-1), random.randint(0, height-1)
        idx1 = y1 * width + x1
        idx2 = y2 * width + x2
        
        if grid[idx1] == 0 and grid[idx2] == 0:
            dist = abs(x1 - x2) + abs(y1 - y2)
            if dist > min_dist:
                return (x1, y1), (x2, y2)
    return None, None

def run_benchmark(limit=None):
    # Добавляем проверку флага из конфига
    if config.USE_SCENARIOS:
        # --- РЕЖИМ СЦЕНАРИЕВ ---
        map_dir = config.MAP_DIR
        scen_dir = config.SCEN_DIR
        print(f"\n🚀 Режим сценариев (Benchmark)")
        header = f"{'#':<4} | {'Scenario File':<20} | {'Algo':<14} | {'Len':<8} | {'Opt':<8} | {'Nodes':<7} | {'Time(ms)':<8}"
        print(header)
        print("-" * len(header))

        scen_files = config.SCENARIO_FILES
        if limit: scen_files = scen_files[:limit]

        for scen_name in scen_files:
            scen_path = os.path.join(scen_dir, scen_name)
            if not os.path.exists(scen_path):
                print(f"⚠️ Файл не найден: {scen_path}")
                continue
            
            tasks = MapParser.parse_scenarios(scen_path)
            if not tasks: continue
            
            map_filename = tasks[0]["map_name"]
            map_path = os.path.join(map_dir, map_filename)
            
            try:
                width, height, grid = MapParser.parse_map(map_path)
                planner = pfc.PathPlanner(width, height, grid)
                run_tasks = tasks[:config.TASKS_PER_SCENARIO]
                
                for task in run_tasks:
                    for name, algo, heur, weight in config.BENCHMARK_ALGORITHMS:
                        res = planner.find_path(task["start"][0], task["start"][1],
                                              task["goal"][0], task["goal"][1],
                                              algo, heur, weight, 8)
                        time_ms = res.execution_time * 1000
                        print(f"{task['id']:<4} | {scen_name[:20]:<20} | {name:<14} | {res.path_length:<8.1f} | {task['optimal_len']:<8.1f} | {res.expanded_nodes:<7} | {time_ms:<8.3f}")
            except Exception as e:
                print(f"Ошибка в {scen_name}: {e}")
    else:
        # --- РЕЖИМ СЛУЧАЙНЫХ КАРТ (если USE_SCENARIOS = False) ---
        map_dir = config.MAP_DIR
        print(f"\n🚀 Режим случайных точек (Benchmark)")
        header = f"{'Map File':<25} | {'Algo':<14} | {'Len':<8} | {'Nodes':<7} | {'Time(ms)':<8}"
        print(header)
        print("-" * len(header))

        map_files = [f for f in os.listdir(map_dir) if f.endswith('.map')]
        map_files.sort()
        if limit: map_files = map_files[:limit]

        for map_name in map_files:
            map_path = os.path.join(map_dir, map_name)
            try:
                width, height, grid = MapParser.parse_map(map_path)
                planner = pfc.PathPlanner(width, height, grid)
                
                points = get_random_valid_points(width, height, grid)
                if not points:
                    print(f"⚠️ Не удалось найти точки для {map_name}")
                    continue
                start, goal = points

                for name, algo, heur, weight in config.BENCHMARK_ALGORITHMS:
                    res = planner.find_path(start[0], start[1], goal[0], goal[1], algo, heur, weight, 8)
                    time_ms = res.execution_time * 1000
                    print(f"{map_name[:25]:<25} | {name:<14} | {res.path_length:<8.1f} | {res.expanded_nodes:<7} | {time_ms:<8.3f}")
            except Exception as e:
                print(f"Ошибка в {map_name}: {e}")

def run_visualization(map_path, algo_key="astar"):
    if not os.path.exists(map_path):
        print(f"❌ Файл не найден: {map_path}")
        return

    # БЕРЕМ АЛГОРИТМ ИЗ СЛОВАРЯ В CONFIG.PY
    if algo_key not in config.VISUAL_ALGOS:
        print(f"⚠️ Алгоритм '{algo_key}' не найден в config.py. Использую 'astar'.")
        algo_key = "astar"
    
    algo_type, heur_type, weight = config.VISUAL_ALGOS[algo_key]

    print(f"\n🎨 Визуализация: {os.path.basename(map_path)}")
    print(f"⚙️  Алгоритм: {algo_key.upper()} (w={weight})")
    
    width, height, grid = MapParser.parse_map(map_path)
    planner = pfc.PathPlanner(width, height, grid)

    start, goal = get_random_valid_points(width, height, grid)
    if not start: 
        print("Не удалось найти точки старта/финиша.")
        return
    
    print(f"Start: {start} -> Goal: {goal}")
    res = planner.find_path(start[0], start[1], goal[0], goal[1], algo_type, heur_type, weight, 8)
    
    if res.found:
        print(f"✅ Путь найден! Длина: {res.path_length:.2f}, Узлов: {res.expanded_nodes}")
        if print_ascii_map:
            print_ascii_map(width, height, grid, res.path, start, goal)
    else:
        print("❌ Путь не найден.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['bench', 'visual'], help="Режим работы")
    parser.add_argument('--map', type=str, help="Путь к файлу карты (для visual)")
    parser.add_argument('--limit', type=int, default=None, help="Лимит карт (для bench)")
    parser.add_argument('--algo', type=str, default='astar', help="Алгоритм для визуализации (ключ из config.py)")

    args = parser.parse_args()

    if args.mode == 'bench':
        run_benchmark(limit=args.limit)
    elif args.mode == 'visual':
        if not args.map:
            print("❌ Укажите карту: --map data/movingai/arena.map")
        else:
            run_visualization(args.map, algo_key=args.algo)