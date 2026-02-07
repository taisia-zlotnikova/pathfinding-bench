import os

class MapParser:
    def __init__(self):
        pass

    @staticmethod
    def parse_map(file_path):
        """
        Читает файл .map (MovingAI format) и возвращает:
        width, height, flat_grid (список int)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл карты не найден: {file_path}")

        with open(file_path, 'r') as f:
            lines = f.readlines()

        height = 0
        width = 0
        grid = []
        
        header_parsed = False
        map_start_index = 0

        # 1. Парсим заголовок
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("height"):
                height = int(line.split()[1])
            elif line.startswith("width"):
                width = int(line.split()[1])
            elif line.startswith("map"):
                map_start_index = i + 1
                header_parsed = True
                break
        
        if not header_parsed:
            raise ValueError("Некорректный формат файла: не найдено ключевое слово 'map'")

        # 2. Парсим сетку
        # Символы MovingAI: 
        # . G S T(trees) @(wall) O(out of bounds)
        # Будем считать проходимым: . G S
        # Непроходимым: @ O T W
        passable_chars = {'.', 'G', 'S'}
        
        current_height = 0
        for i in range(map_start_index, len(lines)):
            line = line = lines[i].strip()
            if not line: 
                continue
            
            # Если строка длиннее ширины (бывает в некоторых файлах), обрезаем
            if len(line) > width:
                line = line[:width]
                
            for char in line:
                if char in passable_chars:
                    grid.append(0) # Свободно
                else:
                    grid.append(1) # Препятствие
            
            current_height += 1
            if current_height >= height:
                break

        if len(grid) != width * height:
            raise ValueError(f"Размер сетки не совпадает. Ожидалось {width*height}, получено {len(grid)}")

        return width, height, grid
    @staticmethod
    def parse_scenarios(scen_path):
        """
        Парсит файл .scen и добавляет порядковый номер задачи.
        """
        scenarios = []
        if not os.path.exists(scen_path):
            return scenarios

        with open(scen_path, 'r') as f:
            lines = f.readlines()
            # Начинаем счетчик с 0 для задач (пропуская строку version)
            task_idx = 0
            for line in lines:
                parts = line.split()
                if not parts or parts[0] == "version":
                    continue
                
                scenarios.append({
                    "id": task_idx, # Сохраняем номер строки/задачи
                    "map_name": parts[1],
                    "start": (int(parts[4]), int(parts[5])),
                    "goal": (int(parts[6]), int(parts[7])),
                    "optimal_len": float(parts[8])
                })
                task_idx += 1
        return scenarios

# Простой тест при запуске файла
if __name__ == "__main__":
    # Создадим временный тестовый файл
    with open("test.map", "w") as f:
        f.write("type octile\nheight 4\nwidth 4\nmap\n.T..\n.@..\n....\n@@@.")
    
    w, h, g = MapParser.parse_map("test.map")
    print(f"Width: {w}, Height: {h}")
    print(f"Grid: {g}")
    # Ожидается: 0, 1, 0, 0, 0, 1, ...
    os.remove("test.map")