import os
import time
import argparse
import torch
import config
from core.map_parser import MapParser
import pathfinding_core as pfc
from gpu.gpu_planner import GPUPathPlanner

# Цвета
C_RESET  = "\033[0m"
C_BOLD   = "\033[1m"
C_GREEN  = "\033[32m"
C_YELLOW = "\033[33m"
C_CYAN   = "\033[36m"

def sync_gpu(device):
    # Просто выбор девайса
    if device.type == "cuda":
        torch.cuda.synchronize()
    elif device.type == "mps":
        torch.mps.synchronize()

def get_uniform_tasks(tasks, count):
    # Хотим выбрать раномерно нужное кол-во сценариев
    total = len(tasks)
    if total <= count or count is None:
        return tasks
    step = total / count
    indices = sorted(list(set([int(i * step) for i in range(count)])))
    return [tasks[i] for i in indices]

def calculate_optimal_chunk(width, height, memory_budget_mb=2048):
    # memory_budget_mb - сколько мегабайт видеопамяти разрешено использовать.
    # Используя ограничение и размер карты считаем более подходящий размер батча

    bytes_per_map = width * height * 8  # ~8 байт на клетку со всеми тензорами
    budget_bytes = memory_budget_mb * 1024 * 1024
    chunk_size = int(budget_bytes // bytes_per_map)

    return max(1, min(2048, chunk_size))

def run_benchmarks(args):
    # вывод параметров тестирования
    print(f"\n{C_BOLD}{C_CYAN}🚀 Умный бенчмарк Cost2Go (CPU vs GPU){C_RESET}")
    print(f"fast_break = {args.fast_break}")
    print(f"Целей на карту: {args.target_tasks} (Uniform) | Радиус: {args.radius} | VRAM Бюджет: {args.vram_mb} MB")
    print(f"{'-'*95}")
    print(f"{'Карта':<25} | {'Размер':<10} | {'Чанк':<6} | {'CPU (сек)':<12} | {'GPU (сек)':<12} | {'Ускорение':<10}")
    print(f"{'-'*95}")

    total_cpu_time = 0.0
    total_gpu_time = 0.0

    for map_type in config.MAP_TYPES:
        scen_dir = os.path.join(config.DATA_DIR, 'scen', map_type)
        map_dir = os.path.join(config.DATA_DIR, 'map', map_type)
        if not os.path.exists(scen_dir): continue

        scen_files = [f for f in os.listdir(scen_dir) if f.endswith('.scen')]
        
        for s_file in scen_files[:args.files_limit]:
            # Парсим сценарии. Используем одни и те же для тестирования на GPU и на CPU
            all_tasks = MapParser.parse_scenarios(os.path.join(scen_dir, s_file))
            if not all_tasks: continue
            if args.target_tasks is None: args.target_tasks = len(all_tasks)
            
            map_name = all_tasks[0]["map_name"]
            if args.map and map_name != args.map: continue
            
            map_path = os.path.join(map_dir, map_name)
            if not os.path.exists(map_path): continue
            
            width, height, grid = MapParser.parse_map(map_path)
            
            # У нас стоит лимит на задания из сценариев, так что выбираем равномерно
            sampled_tasks = get_uniform_tasks(all_tasks, args.target_tasks)
            agents = [t["start"] for t in sampled_tasks]
            goals = [t["goal"] for t in sampled_tasks]
            B = len(agents)
            if B == 0: continue

            # Подбираем нужный ращмер чанка
            chunk_size = calculate_optimal_chunk(width, height, memory_budget_mb=args.vram_mb)

            cpu_planner = pfc.PathPlanner(width, height, grid)
            gpu_planner = GPUPathPlanner(width, height, grid)

            # Прогрев GPU
            gpu_planner.get_cost2go_windows_batch([agents[0]], [goals[0]], args.radius)
            sync_gpu(gpu_planner.device)

            # ------------------
            #        GPU
            # -----------------
            gpu_time = 0.0
            for i in range(0, B, chunk_size):
                chunk_agents = agents[i : i + chunk_size]
                chunk_goals = goals[i : i + chunk_size]
                
                t0 = time.perf_counter()
                gpu_planner.get_cost2go_windows_batch(chunk_agents, chunk_goals, args.radius)
                sync_gpu(gpu_planner.device)
                gpu_time += time.perf_counter() - t0

            # ------------------
            #        CPU
            # -----------------
            t0 = time.perf_counter()
            for i in range(B):
                cpu_planner.get_cost2go_window(agents[i][0], agents[i][1], goals[i][0], goals[i][1], args.radius, 4, args.fast_break)
            cpu_time = time.perf_counter() - t0

            # Вывод результатов
            speedup = cpu_time / gpu_time if gpu_time > 0 else 0
            color = C_GREEN if speedup > 1 else C_YELLOW
            size_str = f"{width}x{height}"
            print(f"{map_name[:25]:<25} | {size_str:<10} | {chunk_size:<6} | {cpu_time:<12.4f} | {gpu_time:<12.4f} | {color}{speedup:.2f}x{C_RESET}")

            total_cpu_time += cpu_time
            total_gpu_time += gpu_time

    print(f"{'-'*95}")
    if total_cpu_time > 0:
        print(f"{C_BOLD}ИТОГО:{C_RESET}")
        print(f"Общее время CPU: {C_YELLOW}{total_cpu_time:.4f} сек{C_RESET}")
        print(f"Общее время GPU: {C_GREEN}{total_gpu_time:.4f} сек{C_RESET}")
        print(f"Среднее ускорение: {C_BOLD}{C_CYAN}{(total_cpu_time / total_gpu_time):.2f}x{C_RESET}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Benchmark Cost2Go CPU vs GPU")
    parser.add_argument('--radius', type=int, default=10, help='Радиус окна')
    parser.add_argument('--target_tasks', type=int, default=20, help='Количество задач из .scen файла для тестирования')
    parser.add_argument('--vram_mb', type=int, default=2048, help='Бюджет видеопамяти (в мегабайтах)')
    parser.add_argument('--files_limit', type=int, default=3, help='Лимит файлов карт для теста')
    parser.add_argument('--map', type=str, default=None, help='Запуск только для конкретной карты')
    parser.add_argument('--fast_break', action=argparse.BooleanOptionalAction, default=True, 
                        help='Останавливать ли подсчет cost2go на cpu (добавьте --no-fast_break чтобы отключить)')
    
    args = parser.parse_args()
    run_benchmarks(args)