import os
import random
from pathlib import Path
import config
from map_parser import MapParser
import pathfinding_core as pfc

try:
    from visualizer import save_map_image, save_cost2go_image
except ImportError:
    save_map_image = None
    save_cost2go_image = None

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
    map_path = args.map
    scen_path = args.scen

    # Логика "умного поиска" карты
    if scen_path and (not map_path or map_path == config.DEFAULT_MAP):
        if not os.path.exists(scen_path):
             scen_part = config.DEFAULT_SCEN.split('/')[0]
             potential_scen = os.path.join(config.DATA_DIR, 'scen', scen_part, scen_path)
             if os.path.exists(potential_scen):
                 scen_path = potential_scen
        
        if os.path.exists(scen_path):
            try:
                tasks = MapParser.parse_scenarios(scen_path)
                if tasks:
                    map_name = tasks[0]["map_name"]
                    for m_type in config.MAP_TYPES:
                        potential = os.path.join(config.DATA_DIR, 'map', m_type, map_name)
                        if os.path.exists(potential):
                            map_path = potential
                            break
            except Exception:
                pass 
    
    if not map_path or not os.path.exists(map_path):
         if map_path == config.DEFAULT_MAP:
             map_path = os.path.join(config.DATA_DIR, 'map', config.DEFAULT_MAP)
         if not os.path.exists(map_path):
            print(f"❌ Ошибка: Карта не найдена по пути {map_path}")
            return

    algo_key = args.algo
    if algo_key not in config.ALGO_REGISTRY:
        print(f"❌ Алгоритм '{algo_key}' не найден. Доступные: {list(config.ALGO_REGISTRY.keys())}")
        return
    algo_type, heur_type, weight = config.ALGO_REGISTRY[algo_key]

    base_map_name = os.path.basename(map_path) if map_path else None
    base_scen_name = os.path.basename(scen_path) if scen_path else None
    if base_scen_name and base_scen_name.endswith('.scen'):
            derived_scen_name = base_scen_name[:-5]
            if base_map_name != derived_scen_name:
                print(f"⚠️ Карта {base_map_name} не совпадает с сценарием {base_scen_name}")
                return

    print(f"📖 Map: {Path(map_path).parent.name}/{Path(map_path).name}")

    width, height, grid = MapParser.parse_map(map_path)
    planner = pfc.PathPlanner(width, height, grid)

    tasks_to_run = []
    if scen_path and os.path.exists(scen_path):
        print(f"📖 Scenarios: {Path(scen_path).parent.name}/{Path(scen_path).name}")
        tasks = MapParser.parse_scenarios(scen_path)
        if args.id is not None:
             if 0 <= args.id < len(tasks):
                 tasks_to_run = [tasks[args.id]]
             else:
                 print(f"❌ ID {args.id} вне диапазона (0-{len(tasks)-1})")
        else:
            limit = args.limit
            tasks_to_run = tasks[:limit]
    else:
        print("📖 Scenarios: Random Generation")
        start, goal = get_random_valid_points(width, height, grid)
        if start:
            tasks_to_run = [{"id": "rnd", "start": start, "goal": goal}]
    
    if not tasks_to_run:
        print("⚠️ Нет задач для выполнения.")
        return

    viz_dir = "visuals"
    os.makedirs(viz_dir, exist_ok=True)
    for task in tasks_to_run:
        task_id = task['id']
        start, goal = task["start"], task["goal"]
        
        c2g_filename = os.path.join(viz_dir, f"c2g_task_{task_id}.png")
        path_filename = os.path.join(viz_dir, f"path_task_{task_id}.png")
        
        print(f"\n🚀 Run Task #{task_id}: {start} -> {goal}")
        
        try:
            c2g_window = planner.get_cost2go_window(
                start[0], start[1], goal[0], goal[1], 
                args.radius, config.CONNECTIVITY
            )
            if save_cost2go_image:
                save_cost2go_image(c2g_window, filename=c2g_filename)
        except Exception as e:
            print(f"⚠️ Ошибка cost2go: {e}")

        res = planner.find_path(start[0], start[1], goal[0], goal[1], 
                               algo_type, heur_type, weight, config.CONNECTIVITY)

        if res.found:
            print(f"✅ Found! Len: {res.path_length:.2f} | Nodes: {res.expanded_nodes} | Time: {res.execution_time*1000:.2f}ms")
            if save_map_image:
                save_map_image(width, height, grid, res.path, start, goal, filename=path_filename)
            print(f"✅ Результаты сохранены в папку: {viz_dir}")
        else:
            print("❌ Path Not Found")