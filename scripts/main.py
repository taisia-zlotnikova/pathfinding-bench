import argparse
import os
import sys
import random
from pathlib import Path

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
    # 1. Определяем пути (если не заданы в аргументах - берутся дефолты из конфига,
    #    которые мы прописали в argparse, но для карт логика поиска сложнее)
    map_path = args.map
    scen_path = args.scen

    # Логика "умного поиска" карты, если она не задана явно, но есть сценарий
    if scen_path and (not map_path or map_path == config.DEFAULT_MAP):
        # Если путь к сценарию относительный и файла нет, ищем в дефолтной папке
        if not os.path.exists(scen_path):
             scen_part = config.DEFAULT_SCEN.split('/')[0] # 'maze'
             potential_scen = os.path.join(config.DATA_DIR, 'scen', scen_part, scen_path)
             if os.path.exists(potential_scen):
                 scen_path = potential_scen
        
        if os.path.exists(scen_path):
            try:
                tasks = MapParser.parse_scenarios(scen_path)
                if tasks:
                    map_name = tasks[0]["map_name"]
                    # Ищем карту по всем папкам типов
                    for m_type in config.MAP_TYPES:
                        potential = os.path.join(config.DATA_DIR, 'map', m_type, map_name)
                        if os.path.exists(potential):
                            map_path = potential
                            break
            except Exception:
                pass # Если не вышло распарсить, остаемся с map_path из аргументов/конфига
    
    # Финальная проверка карты
    if not map_path or not os.path.exists(map_path):
         # Пробуем добавить полный путь к дефолтной карте
         if map_path == config.DEFAULT_MAP:
             map_path = os.path.join(config.DATA_DIR, 'map', config.DEFAULT_MAP)
         
         if not os.path.exists(map_path):
            print(f"❌ Ошибка: Карта не найдена по пути {map_path}")
            print(f"   Проверьте config.py или передайте --map")
            return

    # 2. Настройка алгоритма
    algo_key = args.algo
    if algo_key not in config.ALGO_REGISTRY:
        print(f"❌ Алгоритм '{algo_key}' не найден. Доступные: {list(config.ALGO_REGISTRY.keys())}")
        return
    algo_type, heur_type, weight = config.ALGO_REGISTRY[algo_key]

    # Проверка карты и сценария
    base_map_name = os.path.basename(map_path) if map_path else None
    base_scen_name = os.path.basename(scen_path) if scen_path else None
    if base_scen_name.endswith('.scen'):
            derived_scen_name = base_scen_name[:-5]
            if base_map_name != derived_scen_name:
                print(f"⚠️ Карта {base_map_name} не совпадает с сценарием {base_scen_name}")
                print(f"Берем карту из сценария.")
                map_path = os.path.join(config.DATA_DIR, 'map', derived_scen_name)

    # 3. Загрузка 
    # print(f"📖 Map: {os.path.basename(map_path)}")
    print(f"📖 Map: {Path(map_path).parent.name}/{Path(map_path).name}")

    width, height, grid = MapParser.parse_map(map_path)
    planner = pfc.PathPlanner(width, height, grid)

    # 4. Определение точек
    tasks_to_run = []
    # print(f"📖 Scenarios: {os.path.basename(scen_path)}")
    print(f"📖 Scenarios: {Path(scen_path).parent.name}/{Path(scen_path).name}")
    
    if scen_path and os.path.exists(scen_path):
        tasks = MapParser.parse_scenarios(scen_path)
        
        # ЛОГИКА ВЫБОРА ЗАДАЧ:
        # Приоритет 1: Если задан ID (в конфиге или аргументах)
        if args.id is not None:
             if 0 <= args.id < len(tasks):
                 tasks_to_run = [tasks[args.id]]
             else:
                 print(f"❌ ID {args.id} вне диапазона (0-{len(tasks)-1})")
        # Приоритет 2: Иначе берем LIMIT (из конфига или аргументов)
        else:
            limit = args.limit # Гарантированно есть число (дефолт из конфига)
            tasks_to_run = tasks[:limit]
    else:
        # Случайные точки
        start, goal = get_random_valid_points(width, height, grid)
        if start:
            tasks_to_run = [{"id": "rnd", "start": start, "goal": goal}]
    
    # 5. Исполнение
    if not tasks_to_run:
        print("⚠️ Нет задач для выполнения.")
        return

    for task in tasks_to_run:
        start, goal = task["start"], task["goal"]
        print(f"\n🚀 Run Task #{task['id']}: {start} -> {goal} using {algo_key.upper()}")
        
        res = planner.find_path(start[0], start[1], goal[0], goal[1], 
                               algo_type, heur_type, weight, config.CONNECTIVITY)

        if res.found:
            print(f"✅ Found! Len: {res.path_length:.2f} | Nodes: {res.expanded_nodes} | Time: {res.execution_time*1000:.2f}ms")
            save_map_image(width, height, grid, res.path)
            if print_ascii_map and (width + height < 150): 
                print_ascii_map(width, height, grid, res.path, start, goal)
        else:
            print("❌ Path Not Found")

def run_bench_logic(args):
    """Логика режима bench"""
    limit = args.limit # Берется из аргументов или конфига автоматически
    print(f"🚀 BENCHMARK MODE (Limit: {limit} tasks/scen)")
    print(f"{'Map':<20} | {'Algo':<12} | {'Len':<8} | {'Nodes':<7} | {'Time(ms)':<8}")
    print("-" * 65)

    for m_type in config.MAP_TYPES:
        scen_dir = os.path.join(config.DATA_DIR, 'scen', m_type)
        map_dir = os.path.join(config.DATA_DIR, 'map', m_type)
        if not os.path.exists(scen_dir): continue

        scen_files = [f for f in os.listdir(scen_dir) if f.endswith('.scen')][:1]
        
        for s_file in scen_files:
            tasks = MapParser.parse_scenarios(os.path.join(scen_dir, s_file))
            if not tasks: continue
            
            map_name = tasks[0]["map_name"]
            if not os.path.exists(os.path.join(map_dir, map_name)): continue
            
            width, height, grid = MapParser.parse_map(os.path.join(map_dir, map_name))
            planner = pfc.PathPlanner(width, height, grid)
            
            for name, algo, heur, w_val in config.EXPERIMENT_ALGORITHMS[:3]:
                for task in tasks[:limit]:
                    res = planner.find_path(task["start"][0], task["start"][1],
                                          task["goal"][0], task["goal"][1],
                                          algo, heur, w_val, config.CONNECTIVITY)
                    print(f"{map_name[:20]:<20} | {name:<12} | {res.path_length:<8.1f} | {res.expanded_nodes:<7} | {res.execution_time*1000:<8.3f}")

def print_hints():
    # Цвета для консоли
    C_RESET  = "\033[0m"
    C_BOLD   = "\033[1m"
    C_GREEN  = "\033[32m"
    C_YELLOW = "\033[33m"
    C_CYAN   = "\033[36m"

    print(f"\n{C_BOLD}💡Нелья запускать без аргументов. \nВнимательно прочитайте README.md и изучите файл config.py.\n")

    print(f"\n{C_BOLD} Краткая подсказка:{C_RESET}")
    print(f"{C_CYAN}{'-'*60}{C_RESET}")

    print(f"{C_BOLD}1. 👁️  Визуализация (Visual Mode){C_RESET}")
    print(f"   Посмотреть, как A* ищет путь на лабиринте:")
    print(f"   {C_GREEN}python3 scripts/main.py visual --map data/map/maze/maze512-1-0.map --algo astar{C_RESET}")
    print(f"   Сравнить с WA* (вес 2.0):")
    print(f"   {C_GREEN}python3 scripts/main.py visual --map data/map/random/random512-10-0.map --algo wastar --weight 2.0{C_RESET}")

    print(f"\n{C_BOLD}2. ⏱️  Бенчмарк (Bench Mode){C_RESET}")
    print(f"   Быстрый тест производительности в консоли:")
    print(f"   {C_GREEN}python3 scripts/main.py bench --limit 20{C_RESET}")

    print(f"\n{C_BOLD}3. 🧪 Эксперименты (Exp Mode){C_RESET}")
    print(f"   Запустить массовые тесты для сбора статистики (CSV):")
    print(f"   {C_GREEN}python3 scripts/main.py exp --mode uniform --count 50{C_RESET}")
    print(f"   Тест конкретной карты:")
    print(f"   {C_GREEN}python3 scripts/main.py exp --map random512-10-0.map --count 100{C_RESET}")

    print(f"\n{C_BOLD}4. 📊 Аналитика (Analyze){C_RESET}")
    print(f"   Построить графики по результатам:")
    print(f"   {C_GREEN}python3 scripts/analyze_results.py{C_RESET}")
    
    print(f"{C_CYAN}{'-'*60}{C_RESET}\n")

def main():
    if len(sys.argv) == 1:
        print_hints()
    parser = argparse.ArgumentParser(description="Grid Pathfinding Tool")
    subparsers = parser.add_subparsers(dest='command', required=True, help='Mode')

    # --- 1. VISUAL ---
    vis_parser = subparsers.add_parser('visual', help='Visualize a path')
    
    # ЗДЕСЬ МЫ СВЯЗЫВАЕМ АРГУМЕНТЫ С CONFIG.PY
    # Если пользователь не введет флаг, argparse подставит значение из config
    vis_parser.add_argument('--map', type=str, default=config.DEFAULT_MAP, 
                            help='Path to .map file')
    vis_parser.add_argument('--scen', type=str, default=config.DEFAULT_SCEN, 
                            help='Path to .scen file')
    vis_parser.add_argument('--algo', type=str, default=config.DEFAULT_ALGO, 
                            choices=config.ALGO_REGISTRY.keys())
    vis_parser.add_argument('--id', type=int, default=config.DEFAULT_VISUAL_ID, 
                            help='Task ID from scenario (overrides limit)')
    vis_parser.add_argument('--limit', type=int, default=config.DEFAULT_VISUAL_LIMIT, 
                            help='Run N tasks sequentially')

    # --- 2. BENCH ---
    bench_parser = subparsers.add_parser('bench', help='Quick console benchmark')
    bench_parser.add_argument('--limit', type=int, default=config.BENCH_LIMIT, 
                              help='Tasks per scenario')

    # --- 3. EXP (EXPERIMENTS) ---
    exp_parser = subparsers.add_parser('exp', help='Run full experiments (CSV)')
    exp_parser.add_argument('--mode', type=str, choices=['uniform', 'all', 'first', 'last'], 
                            default=config.EXP_SAMPLING_MODE, help='Sampling mode')
    exp_parser.add_argument('--count', type=int, default=config.EXP_SAMPLING_COUNT, 
                            help='Tasks count per map')
    exp_parser.add_argument('--map', type=str, default=config.EXP_TARGET_MAP, 
                            help='Target map name (e.g. maze512-1-0.map)')

    args = parser.parse_args()

    if args.command == 'visual':
        run_visual_logic(args)
    elif args.command == 'bench':
        run_bench_logic(args)
    elif args.command == 'exp':
        # Передаем аргументы напрямую, они уже заполнены дефолтами из конфига
        run_experiments_logic(
            sampling_mode=args.mode,
            sampling_count=args.count,
            target_map=args.map
        )

if __name__ == "__main__":
    main()