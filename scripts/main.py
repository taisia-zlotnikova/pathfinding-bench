import os
import random
import argparse
import config  # <--- ИМПОРТИРУЕМ НАШ КОНФИГ
import pathfinding_core as pfc # Теперь pfc доступен, так как config настроил sys.path

from map_parser import MapParser

# Пытаемся импортировать визуализатор
try:
    from visualizer import print_ascii_map
except ImportError:
    print_ascii_map = None

def get_random_valid_points(width, height, grid, min_dist=10):
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
    data_dir = config.DATA_DIR # Берем путь из конфига
    
    print(f"\n🚀 Запуск бенчмарка. Папка: {data_dir}")
    print(f"{'Map':<20} | {'Algorithm':<15} | {'Found':<5} | {'Len':<8} | {'Nodes':<8} | {'Time(ms)':<8}")
    print("-" * 90)

    if not os.path.exists(data_dir):
        print(f"❌ Папка с картами не найдена: {data_dir}")
        return

    map_files = [f for f in os.listdir(data_dir) if f.endswith('.map')]
    map_files.sort()

    if limit is not None:
        map_files = map_files[:limit]

    for map_file in map_files:
        full_path = os.path.join(data_dir, map_file)
        try:
            width, height, grid = MapParser.parse_map(full_path)
            planner = pfc.PathPlanner(width, height, grid)
            start, goal = get_random_valid_points(width, height, grid)
            
            if not start: continue

            # ИСПОЛЬЗУЕМ СПИСОК АЛГОРИТМОВ ИЗ CONFIG.PY
            for name, algo, heur, weight in config.BENCHMARK_ALGORITHMS:
                res = planner.find_path(start[0], start[1], goal[0], goal[1], algo, heur, weight, 8)
                
                found = "Yes" if res.found else "No"
                print(f"{map_file[:20]:<20} | {name:<15} | {found:<5} | {res.path_length:<8.1f} | {res.expanded_nodes:<8} | {res.execution_time*1000:<8.3f}")
            print("-" * 90)
        except Exception as e:
            print(f"Error parsing {map_file}: {e}")

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