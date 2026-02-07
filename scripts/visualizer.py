def print_ascii_map(width, height, grid, path=None, start=None, goal=None):
    """
    Рисует карту в консоли.
    Условные обозначения:
    . - пусто
    # - стена
    S - старт
    G - цель
    * - путь
    """
    # Преобразуем путь в множество для быстрого поиска (O(1))
    path_set = set(path) if path else set()
    
    # Символы
    CHAR_EMPTY = '.'
    CHAR_WALL = '#'
    CHAR_PATH = '*'
    CHAR_START = 'S'
    CHAR_GOAL = 'G'
    
    print("-" * (width + 2))
    
    for y in range(height):
        row_str = "|"
        for x in range(width):
            idx = y * width + x
            char_to_print = CHAR_EMPTY
            
            # 1. Базовая карта
            if grid[idx] == 1:
                char_to_print = CHAR_WALL
            
            # 2. Путь (рисуем поверх пустого места)
            if (x, y) in path_set and grid[idx] == 0:
                char_to_print = CHAR_PATH
            
            # 3. Старт и Цель (рисуем поверх всего)
            if start and (x, y) == start:
                char_to_print = CHAR_START
            elif goal and (x, y) == goal:
                char_to_print = CHAR_GOAL
                
            row_str += char_to_print
        row_str += "|"
        print(row_str)
        
    print("-" * (width + 2))

from PIL import Image, ImageDraw

def save_map_image(width, height, grid, path, filename="path_viz.png"):
    """
    Генерирует изображение карты с путем.
    """
    cell_size = 10  # Размер одной клетки в пикселях
    img_width = width * cell_size
    img_height = height * cell_size
    
    # Цвета (RGB)
    COLOR_WALL = (0, 0, 0)       # Черный
    COLOR_FREE = (255, 255, 255) # Белый
    COLOR_PATH = (255, 0, 0)     # Красный
    COLOR_START = (0, 255, 0)    # Зеленый
    COLOR_GOAL = (0, 0, 255)     # Синий

    img = Image.new("RGB", (img_width, img_height), COLOR_FREE)
    pixels = img.load()

    # 1. Рисуем стены
    for y in range(height):
        for x in range(width):
            if grid[y * width + x] == 1: # 1 - это стена
                # Закрашиваем квадрат
                for i in range(cell_size):
                    for j in range(cell_size):
                        pixels[x * cell_size + i, y * cell_size + j] = COLOR_WALL

    # 2. Рисуем путь
    if path:
        draw = ImageDraw.Draw(img)
        # Рисуем линию через центры клеток
        line_points = []
        for (x, y) in path:
            center_x = x * cell_size + cell_size // 2
            center_y = y * cell_size + cell_size // 2
            line_points.append((center_x, center_y))
        
        # Рисуем саму линию (шириной 2 пикселя)
        draw.line(line_points, fill=COLOR_PATH, width=2)
        
        # Рисуем старт и финиш кружочками
        sx, sy = path[0]
        gx, gy = path[-1]
        
        r = cell_size // 3
        draw.ellipse((sx*cell_size+r, sy*cell_size+r, sx*cell_size+2*r, sy*cell_size+2*r), fill=COLOR_START)
        draw.ellipse((gx*cell_size+r, gy*cell_size+r, gx*cell_size+2*r, gy*cell_size+2*r), fill=COLOR_GOAL)

    img.save(filename)
    print(f"🖼️ Карта сохранена в {filename}")