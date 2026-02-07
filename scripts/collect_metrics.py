import os
import argparse
import pandas as pd
import time
import config
import pathfinding_core as pfc
from map_parser import MapParser

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def collect_metrics(task_type, output_file="results.csv"):
    scen_root = os.path.join(config.BASE_DATA_DIR, "scen")
    map_root = os.path.join(config.BASE_DATA_DIR, "map")
    
    target_scen_dir = os.path.join(scen_root, task_type)
    if not os.path.exists(target_scen_dir):
        print(f"❌ Папка сценариев не найдена: {target_scen_dir}")
        return

    results = []
    print(f"🚀 Запуск бенчмарка: {task_type} (Связность: {config.CONNECTIVITY})")

    scen_files = [f for f in os.listdir(target_scen_dir) if f.endswith(".scen")]
    
    for scen_file in scen_files:
        scen_path = os.path.join(target_scen_dir, scen_file)
        tasks = MapParser.parse_scenarios(scen_path)
        if not tasks: continue
        
        # Получаем имя карты и загружаем её
        map_name = tasks[0]["map_name"]
        map_path = os.path.join(map_root, task_type, map_name)

        if not os.path.exists(map_path):
            print(f"⚠️ Карта {map_name} не найдена. Пропуск.")
            continue

        print(f"📄 Обработка: {scen_file} ({len(tasks)} задач)")
        width, height, grid = MapParser.parse_map(map_path)
        planner = pfc.PathPlanner(width, height, grid)

        # Ограничиваем количество задач согласно конфигу
        tasks_to_run = tasks[:config.TASKS_PER_SCENARIO]

        for task in tasks_to_run:
            for algo_name, algo_type, heur, weight in config.BENCHMARK_ALGORITHMS:
                
                # Запуск алгоритма
                res = planner.find_path(
                    task["start"][0], task["start"][1],
                    task["goal"][0], task["goal"][1],
                    algo_type, heur, weight, config.CONNECTIVITY
                )

                if res.found:
                    # Suboptimality
                    # Насколько найденный путь длиннее оптимального (в %)
                    optimal = task["optimal_len"]
                    subopt = 0.0
                    if optimal > 0:
                        subopt = (res.path_length - optimal) / optimal * 100

                    results.append({
                        "Map": map_name,
                        "Scenario": scen_file,
                        "Algorithm": algo_name,
                        "Heuristic": str(heur).split('.')[-1], # красивое имя эвристики
                        "Weight": weight,
                        "Time (ms)": res.execution_time * 1000, # 
                        "Expanded Nodes": res.expanded_nodes,   # 
                        "Path Length": res.path_length,         # 
                        "Optimal Length": optimal,
                        "Suboptimality (%)": subopt,            # 
                        "Success": True
                    })
                else:
                    # Если путь не найден (чего быть не должно на корректных тестах)
                    results.append({
                        "Map": map_name,
                        "Scenario": scen_file,
                        "Algorithm": algo_name,
                        "Success": False
                    })

    if results:
        df = pd.DataFrame(results)
        # Сохраняем в общую папку results
        ensure_dir("results")
        final_path = os.path.join("results", output_file)
        df.to_csv(final_path, index=False)
        print(f"✅ Результаты сохранены: {final_path}")
        print(f"📊 Всего запусков: {len(df)}")
        print(df.groupby("Algorithm")[["Time (ms)", "Expanded Nodes", "Suboptimality (%)"]].mean())
    else:
        print("⚠️ Результаты пусты.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', type=str, default="maze", help="Тип карт (maze, random, etc)")
    parser.add_argument('--output', type=str, default="benchmark_results.csv")
    args = parser.parse_args()
    
    collect_metrics(args.type, args.output)