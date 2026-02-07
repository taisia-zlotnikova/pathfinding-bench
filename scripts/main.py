import os
import random
import argparse
import config  
import pathfinding_core as pfc

from map_parser import MapParser

try:
    from visualizer import print_ascii_map
except ImportError:
    print_ascii_map = None

def get_random_valid_points(width, height, grid, min_dist=2): # Уменьшили дистанцию
    max_attempts = 1000
    for _ in range(max_attempts):
        x1, y1 = random.randint(0, width-1), random.randint(0, height-1)
        x2, y2 = random.randint(0, width-1), random.randint(0, height-1)
        idx1 = y1 * width + x1
        idx2 = y2 * width + x2
        
        if grid[idx1] == 0 and grid[idx2] == 0:
            # Считаем Манхэттенское расстояние для простоты
            dist = abs(x1 - x2) + abs(y1 - y2)
            if dist >= min_dist:
                return (x1, y1), (x2, y2)
    return None, None

def run_benchmark(limit=None):
    if config.USE_SCENARIOS:
        # --- РЕЖИМ СЦЕНАРИЕВ ---
        map_dir = config.MAP_DIR
        scen_dir = config.SCEN_DIR
        print(f"\n🚀 Режим сценариев (Benchmark) | Связность: {config.CONNECTIVITY}")
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
            
            map_path = os.path.join(map_dir, tasks[0]["map_name"])
            if not os.path.exists(map_path):
                print(f"❌ Карта не найдена: {tasks[0]['map_name']}")
                continue

            width, height, grid = MapParser.parse_map(map_path)
            planner = pfc.PathPlanner(width, height, grid)
            
            for task in tasks[:config.TASKS_PER_SCENARIO]:
                for name, algo, heur, weight in config.BENCHMARK_ALGORITHMS:
                    res = planner.find_path(task["start"][0], task["start"][1],
                                          task["goal"][0], task["goal"][1],
                                          algo, heur, weight, config.CONNECTIVITY) # Используем конфиг
                    time_ms = res.execution_time * 1000
                    print(f"{task['id']:<4} | {scen_name[:20]:<20} | {name:<14} | {res.path_length:<8.1f} | {task['optimal_len']:<8.1f} | {res.expanded_nodes:<7} | {time_ms:<8.3f}")
    else:
        # --- РЕЖИМ СЛУЧАЙНЫХ ТОЧЕК ---
        map_dir = config.MAP_DIR
        print(f"\n🚀 Режим случайных точек (Benchmark) | Связность: {config.CONNECTIVITY}")
        header = f"{'Map File':<25} | {'Algo':<14} | {'Len':<8} | {'Nodes':<7} | {'Time(ms)':<8}"
        print(header)
        print("-" * len(header))

        map_files = [f for f in os.listdir(map_dir) if f.endswith('.map')]
        map_files.sort()
        if limit: map_files = map_files[:limit]

        for map_name in map_files:
            map_path = os.path.join(map_dir, map_name)
            width, height, grid = MapParser.parse_map(map_path)
            planner = pfc.PathPlanner(width, height, grid)
            
            points = get_random_valid_points(width, height, grid)
            if not points: continue
            start, goal = points

            for name, algo, heur, weight in config.BENCHMARK_ALGORITHMS:
                res = planner.find_path(start[0], start[1], goal[0], goal[1], algo, heur, weight, config.CONNECTIVITY) # Используем конфиг
                time_ms = res.execution_time * 1000
                print(f"{map_name[:25]:<25} | {name:<14} | {res.path_length:<8.1f} | {res.expanded_nodes:<7} | {time_ms:<8.3f}")

def run_visualization(map_path, algo_key="astar", scen_path=None, task_id=0):
    if not os.path.exists(map_path):
        print(f"❌ Карта не найдена: {map_path}")
        return

    # Получаем настройки алгоритма
    algo_type, heur_type, weight = config.VISUAL_ALGOS.get(algo_key, config.VISUAL_ALGOS["astar"])

    print(f"📖 Загрузка карты: {map_path}...")
    width, height, grid = MapParser.parse_map(map_path)
    planner = pfc.PathPlanner(width, height, grid)

    # Выбор точек
    if scen_path and os.path.exists(scen_path):
        tasks = MapParser.parse_scenarios(scen_path)
        if task_id < len(tasks):
            task = tasks[task_id]
            start, goal = task["start"], task["goal"]
            print(f"📋 Задача #{task_id} из сценария: Start {start} -> Goal {goal}")
        else:
            print(f"⚠️ Задача #{task_id} не найдена, использую случайные точки.")
            start, goal = get_random_valid_points(width, height, grid)
    else:
        start, goal = get_random_valid_points(width, height, grid)

    if not start:
        print("❌ Ошибка: не удалось найти свободные точки на карте.")
        return

    # ЗАПУСК ПОИСКА
    print(f"🔎 Поиск пути (Алгоритм: {algo_key.upper()}, Сетка: {config.CONNECTIVITY})...")
    res = planner.find_path(start[0], start[1], goal[0], goal[1], 
                           algo_type, heur_type, weight, 
                           config.CONNECTIVITY)

    if res.found:
        print(f"✅ Путь найден! Длина: {res.path_length:.2f}")
        if print_ascii_map:
            print_ascii_map(width, height, grid, res.path, start, goal)
        else:
            print("❌ Ошибка: Функция print_ascii_map не найдена. Проверьте файл visualizer.py!")
    else:
        print(f"❌ Путь НЕ найден. Проверьте, что точки {start} и {goal} не заблокированы стенами.")
        # Даже если путь не найден, отрисуем карту со стартом и финишем для проверки
        if print_ascii_map:
            print("\nОтрисовка карты без пути (проверка точек):")
            print_ascii_map(width, height, grid, [], start, goal)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['bench', 'visual'])
    parser.add_argument('--map', type=str)
    parser.add_argument('--scen', type=str)
    parser.add_argument('--id', type=int, default=0)
    parser.add_argument('--algo', type=str, default='astar')
    parser.add_argument('--limit', type=int, default=None)
    
    args = parser.parse_args()

    if args.mode == 'bench':
        run_benchmark(limit=args.limit)
    elif args.mode == 'visual':
        # 1. Если указан сценарий, а карта нет — пытаемся найти карту сами
        if args.scen and not args.map:
            tasks = MapParser.parse_scenarios(args.scen)
            if tasks:
                map_name = tasks[0]["map_name"]
                # Склеиваем путь к карте на основе папки из конфига
                args.map = os.path.join(config.MAP_DIR, map_name)
                print(f"🔍 Авто-поиск карты: {args.map}")

        # 2. Проверяем наличие файла карты
        if not args.map or not os.path.exists(args.map):
            print(f"❌ Ошибка: Файл карты не найден.\ Укажите путь через --map или сценарий через --scen. Проверьте config.DATA_DIR и проверьте config.MAP_DIR")
        else:
            # 3. Вызываем визуализацию со всеми параметрами
            run_visualization(
                map_path=args.map, 
                algo_key=args.algo, 
                scen_path=args.scen, 
                task_id=args.id
            )