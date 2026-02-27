import argparse
import sys
import os

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import config
from commands.run_visual import run_visual_logic
from commands.benchmark_tester import run_bench_logic
from commands.run_experiments import run_experiments_logic
from commands.bench_c2g import run_benchmarks as run_bench_gpu_logic

def print_hints():
    # Цвета для консоли
    C_RESET  = "\033[0m"
    C_BOLD   = "\033[1m"
    C_GREEN  = "\033[32m"
    C_CYAN   = "\033[36m"

    print(f"\n{C_BOLD}💡 Нельзя запускать без аргументов. \nВнимательно прочитайте README.md и изучите файл config.py.\n")
    print(f"{C_BOLD} Краткая подсказка:{C_RESET}")
    print(f"{C_CYAN}{'-'*60}{C_RESET}")

    print(f"{C_BOLD}1. 👁️  Визуализация (Visual Mode){C_RESET}")
    print(f"   {C_GREEN}python3 scripts/main.py visual --map data/map/maze/maze512-1-0.map --algo astar{C_RESET}")

    print(f"\n{C_BOLD}2. ⏱️  Бенчмарк CPU (Bench Mode){C_RESET}")
    print(f"   {C_GREEN}python3 scripts/main.py bench --limit 20{C_RESET}")

    print(f"\n{C_BOLD}3. 🚀 Бенчмарк GPU vs CPU Cost2Go{C_RESET}")
    print(f"   {C_GREEN}python3 scripts/main.py bench-gpu --target_tasks 500{C_RESET}")

    print(f"\n{C_BOLD}4. 🧪 Эксперименты (Exp Mode){C_RESET}")
    print(f"   {C_GREEN}python3 scripts/main.py exp --mode uniform --count 50{C_RESET}")

    print(f"\n{C_BOLD}5. 📊 Аналитика (Analyze){C_RESET}")
    print(f"   {C_GREEN}python3 scripts/analyze_results.py{C_RESET}")
    print(f"{C_CYAN}{'-'*60}{C_RESET}\n")

def main():
    if len(sys.argv) == 1:
        print_hints()
        
    parser = argparse.ArgumentParser(description="Grid Pathfinding Tool")
    subparsers = parser.add_subparsers(dest='command', required=True, help='Режимы работы')

    # --- 1. VISUAL ---
    vis_parser = subparsers.add_parser('visual', help='Визуализация алгоритмов на карте')
    vis_parser.add_argument('--map', type=str, default=config.DEFAULT_MAP, help='Path to .map file')
    vis_parser.add_argument('--scen', type=str, default=config.DEFAULT_SCEN, help='Path to .scen file')
    vis_parser.add_argument('--algo', type=str, default=config.DEFAULT_ALGO, choices=config.ALGO_REGISTRY.keys())
    vis_parser.add_argument('--id', type=int, default=config.DEFAULT_VISUAL_ID, help='Task ID from scenario')
    vis_parser.add_argument('--limit', type=int, default=config.DEFAULT_VISUAL_LIMIT, help='Run N tasks sequentially')
    vis_parser.add_argument('--radius', type=int, default=config.RADIUS, help='Radius of window for cost2go')

    # --- 2. BENCH (CPU) ---
    bench_parser = subparsers.add_parser('bench', help='Быстрый бенчмарк поиска пути в консоль')
    bench_parser.add_argument('--limit', type=int, default=config.BENCH_LIMIT, help='Tasks per scenario')

    # --- 3. EXP (EXPERIMENTS) ---
    exp_parser = subparsers.add_parser('exp', help='Массовые эксперименты (CSV)')
    exp_parser.add_argument('--mode', type=str, choices=['uniform', 'all', 'first', 'last'], 
                            default=config.EXP_SAMPLING_MODE, help='Sampling mode')
    exp_parser.add_argument('--count', type=int, default=config.EXP_SAMPLING_COUNT, help='Tasks count per map')
    exp_parser.add_argument('--map', type=str, default=config.EXP_TARGET_MAP, help='Target map name')

    # --- 4. BENCH-GPU (Cost2Go) ---
    gpu_parser = subparsers.add_parser('bench-gpu', help='Умный бенчмарк Cost2Go: CPU vs GPU')
    gpu_parser.add_argument('--radius', type=int, default=10, help='Радиус окна')
    gpu_parser.add_argument('--target_tasks', type=int, default=20, help='Количество задач из .scen файла для тестирования')
    gpu_parser.add_argument('--batch_size', type=int, default=128, help='Размер батчей')
    gpu_parser.add_argument('--files_limit', type=int, default=3, help='Лимит файлов карт для теста')
    gpu_parser.add_argument('--map', type=str, default=None, help='Запуск только для конкретной карты')
    gpu_parser.add_argument('--fast_break', action=argparse.BooleanOptionalAction, default=True, 
                            help='Останавливать ли подсчет cost2go на CPU')

    args = parser.parse_args()

    if args.command == 'visual':
        run_visual_logic(args)
    elif args.command == 'bench':
        run_bench_logic(args)
    elif args.command == 'exp':
        run_experiments_logic(sampling_mode=args.mode, sampling_count=args.count, target_map=args.map)
    elif args.command == 'bench-gpu':
        run_bench_gpu_logic(args)

if __name__ == "__main__":
    main()