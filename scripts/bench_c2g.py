import os
import sys
import time
import argparse
import config
from map_parser import MapParser
import pathfinding_core as pfc
from gpu_planner import GPUPathPlanner
import torch

# Цвета для красивого вывода
C_RESET  = "\033[0m"
C_BOLD   = "\033[1m"
C_GREEN  = "\033[32m"
C_YELLOW = "\033[33m"
C_CYAN   = "\033[36m"

def sync_gpu(device):
    """Синхронизация для точного замера времени на GPU"""
    if device.type == "cuda":
        torch.cuda.synchronize()
    elif device.type == "mps":
        torch.mps.synchronize()

def run_benchmarks(args):
    print(f"\n{C_BOLD}{C_CYAN}🚀 Запуск масштабного бенчмарка Cost2Go (CPU vs GPU){C_RESET}")
    print(f"Радиус окна: {args.radius} | Размер батча: {args.batch_size}")
    print(f"{'-'*85}")
    print(f"{'Карта':<25} | {'Задач':<7} | {'CPU (сек)':<12} | {'GPU (сек)':<12} | {'Ускорение':<10}")
    print(f"{'-'*85}")

    total_cpu_time = 0.0
    total_gpu_time = 0.0
    total_tasks = 0

    # Перебор типов карт из конфига
    for map_type in config.MAP_TYPES:
        scen_dir = os.path.join(config.DATA_DIR, 'scen', map_type)
        map_dir = os.path.join(config.DATA_DIR, 'map', map_type)
        
        if not os.path.exists(scen_dir): continue

        scen_files = [f for f in os.listdir(scen_dir) if f.endswith('.scen')]
        
        # Ограничим количество файлов сценариев для быстрого теста, если не указано иное
        for s_file in scen_files[:args.files_limit]:
            tasks = MapParser.parse_scenarios(os.path.join(scen_dir, s_file))
            if not tasks: continue
            
            map_name = tasks[0]["map_name"]
            if args.map and map_name != args.map: continue
                
            map_path = os.path.join(map_dir, map_name)
            if not os.path.exists(map_path): continue
            
            # Чтение карты
            width, height, grid = MapParser.parse_map(map_path)
            
            # Инициализация планировщиков
            cpu_planner = pfc.PathPlanner(width, height, grid)
            gpu_planner = GPUPathPlanner(width, height, grid)
            
            # Формирование пакета задач
            batch_tasks = tasks[:args.batch_size]
            agents = [t["start"] for t in batch_tasks]
            goals = [t["goal"] for t in batch_tasks]
            B = len(agents)
            if B == 0: continue

            # --- ПРОГРЕВ GPU ---
            # Первый вызов PyTorch тратит время на выделение памяти, его не учитываем
            gpu_planner.get_cost2go_windows_batch([agents[0]], [goals[0]], args.radius)
            sync_gpu(gpu_planner.device)

            # --- ЗАМЕР GPU (Пакетный запуск) ---
            t0 = time.perf_counter()
            gpu_planner.get_cost2go_windows_batch(agents, goals, args.radius)
            sync_gpu(gpu_planner.device)
            gpu_time = time.perf_counter() - t0

            # --- ЗАМЕР CPU (Последовательный запуск) ---
            # В C++ реализации используется connectivity=4 для точного совпадения с BFS PyTorch
            t0 = time.perf_counter()
            for i in range(B):
                cpu_planner.get_cost2go_window(agents[i][0], agents[i][1], goals[i][0], goals[i][1], args.radius, 4)
            cpu_time = time.perf_counter() - t0

            # --- ПОДСЧЕТ И ВЫВОД ---
            speedup = cpu_time / gpu_time if gpu_time > 0 else 0
            color = C_GREEN if speedup > 1 else C_YELLOW
            
            print(f"{map_name[:25]:<25} | {B:<7} | {cpu_time:<12.4f} | {gpu_time:<12.4f} | {color}{speedup:.2f}x{C_RESET}")

            total_cpu_time += cpu_time
            total_gpu_time += gpu_time
            total_tasks += B

    print(f"{'-'*85}")
    if total_tasks > 0:
        avg_speedup = total_cpu_time / total_gpu_time
        print(f"{C_BOLD}ИТОГО:{C_RESET} Обработано {total_tasks} задач.")
        print(f"Общее время CPU: {C_YELLOW}{total_cpu_time:.4f} сек{C_RESET}")
        print(f"Общее время GPU: {C_GREEN}{total_gpu_time:.4f} сек{C_RESET}")
        print(f"Среднее ускорение: {C_BOLD}{C_CYAN}{avg_speedup:.2f}x{C_RESET}")
    else:
        print("Не найдено подходящих задач для тестирования.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cost2Go Benchmark CPU vs GPU")
    parser.add_argument('--radius', type=int, default=10, help='Радиус окна для cost2go')
    parser.add_argument('--batch_size', type=int, default=1024, help='Количество пар агент-цель для тестирования (размер батча)')
    parser.add_argument('--files_limit', type=int, default=3, help='Количество файлов сценариев для проверки в каждой папке')
    parser.add_argument('--map', type=str, default=None, help='Запуск только для конкретной карты (опционально)')
    
    args = parser.parse_args()
    run_benchmarks(args)