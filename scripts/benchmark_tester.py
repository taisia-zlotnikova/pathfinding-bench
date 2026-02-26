import os
import sys
import config
import pathfinding_core as pfc
from map_parser import MapParser

def run_bench_logic(args):
    """Логика режима bench (быстрый консольный прогон)"""
    limit = args.limit
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

def run_scen_test(scen_file, num_tasks=10):
    scen_path = os.path.join(config.DATA_DIR, scen_file)
    tasks = MapParser.parse_scenarios(scen_path)
    
    # Ищем карту, указанную в сценарии
    map_name = tasks[0]["map"]
    map_path = os.path.join(config.DATA_DIR, map_name)
    
    width, height, grid = MapParser.parse_map(map_path)
    planner = pfc.PathPlanner(width, height, grid)

    print(f"\n🧪 Тестирование сценария: {scen_file} (Карта: {map_name})")
    print(f"{'#':<3} | {'Algo':<10} | {'Result Len':<10} | {'Optimal':<10} | {'Status':<10}")
    print("-" * 55)

    for i, task in enumerate(tasks[:num_tasks]):
        # Берем классический A* для проверки точности
        res = planner.find_path(
            task["start"][0], task["start"][1], 
            task["goal"][0], task["goal"][1],
            pfc.AlgorithmType.AStar, pfc.HeuristicType.Octile, 1.0, 8
        )
        
        # Сравниваем с эталоном (с небольшой погрешностью из-за float)
        diff = abs(res.path_length - task["optimal_len"])
        status = "✅ OK" if diff < 0.001 else f"❌ ERR ({diff:.2f})"
        
        print(f"{i:<3} | {'A*':<10} | {res.path_length:<10.2f} | {task['optimal_len']:<10.2f} | {status}")

if __name__ == "__main__":
    # Замените на имя вашего .scen файла
    example_scen = "maze512-1-0.map.scen" 
    if os.path.exists(os.path.join(config.DATA_DIR, example_scen)):
        run_scen_test(example_scen)
    else:
        print("Пожалуйста, положите .map и .map.scen файлы в папку data/map/, data/scen")