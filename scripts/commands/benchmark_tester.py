import os
import sys
import config
import pathfinding_core as pfc
from core.map_parser import MapParser

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

if __name__ == "__main__":
    pass