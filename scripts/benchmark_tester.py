import os
import sys
import config
import pathfinding_core as pfc
from map_parser import MapParser

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
        print("Пожалуйста, положите .map и .map.scen файлы в папку data/movingai/")