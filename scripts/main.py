import argparse
import os
import sys
import random

# Подключаем наши модули
import config
from run_experiments import run_experiments_logic
from map_parser import MapParser
import pathfinding_core as pfc

try:
    from visualizer import print_ascii_map, save_map_image
except ImportError:
    print_ascii_map = None

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_random_valid_points(width, height, grid, min_dist=2):
    max_attempts = 1000
    for _ in range(max_attempts):
        x1, y1 = random.randint(0, width-1), random.randint(0, height-1)
        x2, y2 = random.randint(0, width-1), random.randint(0, height-1)
        idx1 = y1 * width + x1
        idx2 = y2 * width + x2
        if grid[idx1] == 0 and grid[idx2] == 0:
            dist = abs(x1 - x2) + abs(y1 - y2)
            if dist >= min_dist:
                return (x1, y1), (x2, y2)
    return None, None

def run_visual_logic(args):
    """Логика режима visual"""
    # 1. Определяем пути
    map_path = args.map
    scen_path = args.scen

    # Если карта не указана, но есть сценарий -> берем карту из сценария
    if scen_path and not map_path:
        if not os.path.exists(scen_path):
             # Попытка найти в дефолтной папке
             scen_path = os.path.join(config.DATA_DIR, 'scen', config.DEFAULT_SCEN.split('/')[0], scen_path)
        
        if os.path.exists(scen_path):
            tasks = MapParser.parse_scenarios(scen_path)
            if tasks:
                map_name = tasks[0]["map_name"]
                # Пытаемся найти карту рекурсивно или в известном месте
                # Упрощение: ищем в config.DATA_DIR/map/<тип>/<имя>
                # Но так как мы не знаем тип, попробуем найти
                for m_type in config.MAP_TYPES:
                    potential = os.path.join(config.DATA_DIR, 'map', m_type, map_name)
                    if os.path.exists(potential):
                        map_path = potential
                        break
    
    # Если карта всё еще не найдена или не указана, берем дефолт
    if not map_path or not os.path.exists(map_path):
         print(f"⚠️ Карта не указана или не найдена. Использую дефолтную: {config.DEFAULT_MAP}")
         map_path = os.path.join(config.DATA_DIR, 'map', config.DEFAULT_MAP)

    if not os.path.exists(map_path):
        print(f"❌ Критическая ошибка: Карта не найдена по пути {map_path}")
        return

    # 2. Настройка алгоритма
    algo_key = args.algo
    if algo_key not in config.ALGO_REGISTRY:
        print(f"❌ Алгоритм '{algo_key}' не найден. Доступные: {list(config.ALGO_REGISTRY.keys())}")
        return
    algo_type, heur_type, weight = config.ALGO_REGISTRY[algo_key]

    # 3. Загрузка
    print(f"📖 Map: {os.path.basename(map_path)}")
    width, height, grid = MapParser.parse_map(map_path)
    planner = pfc.PathPlanner(width, height, grid)

    # 4. Определение точек
    tasks_to_run = []
    
    if scen_path and os.path.exists(scen_path):
        tasks = MapParser.parse_scenarios(scen_path)
        if args.id is not None:
             # Одна конкретная задача
             if 0 <= args.id < len(tasks):
                 tasks_to_run = [tasks[args.id]]
             else:
                 print(f"❌ ID {args.id} вне диапазона (0-{len(tasks)-1})")
        else:
            # Лимит задач
            limit = args.limit if args.limit else len(tasks)
            tasks_to_run = tasks[:limit]
    else:
        # Случайные точки
        start, goal = get_random_valid_points(width, height, grid)
        if start:
            tasks_to_run = [{"id": "rnd", "start": start, "goal": goal}]
    
    # 5. Исполнение
    for task in tasks_to_run:
        start, goal = task["start"], task["goal"]
        print(f"\n🚀 Run Task #{task['id']}: {start} -> {goal} using {algo_key.upper()}")
        
        res = planner.find_path(start[0], start[1], goal[0], goal[1], 
                               algo_type, heur_type, weight, config.CONNECTIVITY)

        if res.found:
            print(f"✅ Found! Len: {res.path_length:.2f} | Nodes: {res.expanded_nodes} | Time: {res.execution_time*1000:.2f}ms")
            if print_ascii_map and (width + height < 150): # Рисуем только если карта не гигантская
                print_ascii_map(width, height, grid, res.path, start, goal)
        else:
            print("❌ Path Not Found")

def run_bench_logic(args):
    """Логика режима bench (быстрый тест в консоль)"""
    limit = args.limit if args.limit else config.BENCH_LIMIT
    print(f"🚀 BENCHMARK MODE (Limit: {limit} tasks/scen)")
    print(f"{'Map':<20} | {'Algo':<12} | {'Len':<8} | {'Nodes':<7} | {'Time(ms)':<8}")
    print("-" * 65)

    # Для примера берем первую попавшуюся карту из конфига или ищем
    # Упрощенная логика: берем все .scen из data/scen/maze (как пример)
    
    # Сканируем типы из конфига
    for m_type in config.MAP_TYPES:
        scen_dir = os.path.join(config.DATA_DIR, 'scen', m_type)
        map_dir = os.path.join(config.DATA_DIR, 'map', m_type)
        if not os.path.exists(scen_dir): continue

        scen_files = [f for f in os.listdir(scen_dir) if f.endswith('.scen')][:1] # Берем 1 файл для теста
        
        for s_file in scen_files:
            tasks = MapParser.parse_scenarios(os.path.join(scen_dir, s_file))
            if not tasks: continue
            
            map_name = tasks[0]["map_name"]
            if not os.path.exists(os.path.join(map_dir, map_name)): continue
            
            width, height, grid = MapParser.parse_map(os.path.join(map_dir, map_name))
            planner = pfc.PathPlanner(width, height, grid)
            
            # Тестируем несколько алгоритмов
            for name, algo, heur, w_val in config.EXPERIMENT_ALGORITHMS[:3]: # Берем первые 3 алгоритма
                for task in tasks[:limit]:
                    res = planner.find_path(task["start"][0], task["start"][1],
                                          task["goal"][0], task["goal"][1],
                                          algo, heur, w_val, config.CONNECTIVITY)
                    print(f"{map_name[:20]:<20} | {name:<12} | {res.path_length:<8.1f} | {res.expanded_nodes:<7} | {res.execution_time*1000:<8.3f}")

def main():
    parser = argparse.ArgumentParser(description="Grid Pathfinding Tool")
    subparsers = parser.add_subparsers(dest='command', required=True, help='Mode')

    # --- 1. VISUAL ---
    vis_parser = subparsers.add_parser('visual', help='Visualize a path')
    vis_parser.add_argument('--map', type=str, help='Path to .map file')
    vis_parser.add_argument('--scen', type=str, help='Path to .scen file')
    vis_parser.add_argument('--algo', type=str, default=config.DEFAULT_ALGO, choices=config.ALGO_REGISTRY.keys())
    vis_parser.add_argument('--id', type=int, help='Task ID from scenario')
    vis_parser.add_argument('--limit', type=int, help='Run N tasks sequentially')

    # --- 2. BENCH ---
    bench_parser = subparsers.add_parser('bench', help='Quick console benchmark')
    bench_parser.add_argument('--limit', type=int, default=10, help='Tasks per scenario')

    # --- 3. EXP (EXPERIMENTS) ---
    exp_parser = subparsers.add_parser('exp', help='Run full experiments (CSV)')
    exp_parser.add_argument('--mode', type=str, choices=['uniform', 'all', 'first', 'last'], help='Sampling mode')
    exp_parser.add_argument('--count', type=int, help='Tasks count per map')
    exp_parser.add_argument('--map', type=str, help='Target map name (e.g. maze512-1-0.map)')

    args = parser.parse_args()

    if args.command == 'visual':
        run_visual_logic(args)
    elif args.command == 'bench':
        run_bench_logic(args)
    elif args.command == 'exp':
        # Передаем аргументы, если они есть. Если нет - там внутри подхватятся дефолты из config
        run_experiments_logic(
            sampling_mode=args.mode,
            sampling_count=args.count,
            target_map=args.map
        )

if __name__ == "__main__":
    main()