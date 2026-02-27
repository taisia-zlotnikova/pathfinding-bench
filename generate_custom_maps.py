import os
import random
import math

def generate_movingai_dataset(map_dir, scen_dir, map_name, width, height, obstacle_prob, num_tasks):
    """
    Генерирует карту и файл сценариев в формате Moving AI.
    """
    # 1. Создаем директории, если их нет
    os.makedirs(map_dir, exist_ok=True)
    os.makedirs(scen_dir, exist_ok=True)

    map_path = os.path.join(map_dir, map_name)
    scen_name = map_name + ".scen"
    scen_path = os.path.join(scen_dir, scen_name)

    print(f"Генерация карты {width}x{height} (Препятствия: {obstacle_prob*100}%)...")
    
    # 2. Генерируем сетку и запоминаем пустые клетки
    grid = []
    free_cells = []
    
    for y in range(height):
        row = []
        for x in range(width):
            if random.random() < obstacle_prob:
                row.append('@')
            else:
                row.append('.')
                free_cells.append((x, y))
        grid.append(row)

    # 3. Сохраняем .map файл
    with open(map_path, 'w') as f:
        f.write("type octile\n")
        f.write(f"height {height}\n")
        f.write(f"width {width}\n")
        f.write("map\n")
        for row in grid:
            f.write("".join(row) + "\n")
            
    print(f"Карта сохранена: {map_path}")
    print(f"Генерация {num_tasks} сценариев...")

    # 4. Сохраняем .scen файл
    with open(scen_path, 'w') as f:
        f.write("version 1.0\n")
        for _ in range(num_tasks):
            start = random.choice(free_cells)
            goal = random.choice(free_cells)
            
            """
            Это !заглушка! реального расстояния. Нужно только для тестирования bench-gpu
            Верные ответы не подсчитаны, но необходимо для парсера
            """
            dummy_length = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
            
            # Формат: bucket \t map_name \t width \t height \t start_x \t start_y \t goal_x \t goal_y \t optimal_length
            line = f"0\t{map_name}\t{width}\t{height}\t{start[0]}\t{start[1]}\t{goal[0]}\t{goal[1]}\t{dummy_length:.8f}\n"
            f.write(line)

    print(f"Сценарии сохранены: {scen_path}")
    print("Готово! Можно запускать бенчмарк.")

if __name__ == "__main__":
    MAP_TYPE = "my_random"
    
    MAP_DIR = os.path.join("data", "map", MAP_TYPE)
    SCEN_DIR = os.path.join("data", "scen", MAP_TYPE)
    
    generate_movingai_dataset(
        map_dir=MAP_DIR,
        scen_dir=SCEN_DIR,
        map_name="random1024-25-custom.map",
        width=1024,
        height=1024,
        obstacle_prob=0.25,
        num_tasks=2000
    )