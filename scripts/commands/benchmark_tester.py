import os
import config
from core.map_parser import MapParser
import pathfinding_core as pfc

def run_bench_logic(args):
    """Логика режима bench (агрегированный консольный прогон)"""
    limit = args.limit
    print(f"🚀 BENCHMARK MODE (Сводка по {limit} задачам на карту)")
    print(f"{'Map':<20} | {'Algo':<12} | {'Tasks':<6} | {'Avg Nodes':<10} | {'Avg Time(ms)':<12}")
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
            
            # Тестируем алгоритмы
            for name, algo, heur, w_val in config.EXPERIMENT_ALGORITHMS[:3]:
                total_time = 0.0
                total_nodes = 0
                success_tasks = 0

                if limit == -1:
                    end = len(tasks)
                else:
                    end = min(limit, len(tasks))
                    
                for task in tasks[:limit]:
                    res = planner.find_path(task["start"][0], task["start"][1],
                                          task["goal"][0], task["goal"][1],
                                          algo, heur, w_val, config.CONNECTIVITY)
                    if res.found:
                        total_time += res.execution_time
                        total_nodes += res.expanded_nodes
                        success_tasks += 1

                # Выводим среднее значение, если хоть один путь найден
                if success_tasks > 0:
                    avg_time_ms = (total_time / success_tasks) * 1000
                    avg_nodes = total_nodes / success_tasks
                    print(f"{map_name[:20]:<20} | {name:<12} | {success_tasks:<6} | {avg_nodes:<10.0f} | {avg_time_ms:<12.3f}")