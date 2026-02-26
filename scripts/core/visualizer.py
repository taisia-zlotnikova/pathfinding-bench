from PIL import Image, ImageDraw

def save_map_image(width, height, grid, path=None, start=None, goal=None, filename="path_viz.png"):
    """
    Визуализация карты, где путь закрашивается целыми клетками.
    """
    # 1. Настройка масштаба (cell_size пикселей на одну клетку)
    if width > 512 or height > 512:
        cell_size = 2  # Совсем мелкие клетки для гигантских карт
    elif width > 256:
        cell_size = 5
    else:
        cell_size = 10
        
    img_width = width * cell_size
    img_height = height * cell_size
    
    # Цвета
    COLOR_WALL = (40, 40, 40)       # Стены (темные)
    COLOR_FREE = (240, 240, 240)    # Пусто (светло-серый)
    COLOR_PATH = (255, 150, 150)    # Путь (нежно-красный, чтобы не перекрывал маркеры)
    COLOR_START = (0, 200, 0)       # Старт (зеленый)
    COLOR_GOAL = (0, 0, 200)        # Цель (синий)

    img = Image.new("RGB", (img_width, img_height), COLOR_FREE)
    draw = ImageDraw.Draw(img)

    # 2. Рисуем стены
    for y in range(height):
        for x in range(width):
            if grid[y * width + x] == 1: # 1 - это стена
                shape = [x * cell_size, y * cell_size, (x + 1) * cell_size, (y + 1) * cell_size]
                draw.rectangle(shape, fill=COLOR_WALL)

    # 3. Закрашиваем клетки ПУТИ
    if path:
        for (x, y) in path:
            shape = [x * cell_size, y * cell_size, (x + 1) * cell_size, (y + 1) * cell_size]
            draw.rectangle(shape, fill=COLOR_PATH)

    # 4. Рисуем маркеры Старта и Финиша (поверх пути)
    def fill_cell(pos, color):
        if pos:
            x, y = pos
            shape = [x * cell_size, y * cell_size, (x + 1) * cell_size, (y + 1) * cell_size]
            draw.rectangle(shape, fill=color, outline=(0,0,0), width=1)

            center_x, center_y = x * cell_size + cell_size // 2, y * cell_size + cell_size // 2
            radius = cell_size * 5
            draw.ellipse([center_x - radius, center_y - radius, center_x + radius, center_y + radius], 
                        fill=None, 
                        outline=color, 
                        width=3)

    fill_cell(start, COLOR_START)
    fill_cell(goal, COLOR_GOAL)

    img.save(filename)
    print(f"🖼️ Карта (плитки) сохранена в {filename}")

def save_cost2go_image(window, filename="cost2go.png"):
    """
    Рисует тепловую карту Cost-2-Go.
    window: 2D список (list of lists), который вернул C++.
    """
    try:
        import numpy as np
    except ImportError:
        print("⚠️ Для визуализации cost2go нужен numpy")
        return

    # Преобразуем в массив для удобства
    grid = np.array(window)
    height, width = grid.shape
    
    # Настройка размера пикселя (сделаем покрупнее, так как окно маленькое, например 11x11)
    cell_size = 40 
    img_width = width * cell_size
    img_height = height * cell_size
    
    img = Image.new("RGB", (img_width, img_height), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Нормализация для цветов: найдем макс значение, исключая -1 (стены)
    valid_values = grid[grid != -1.0]
    max_val = valid_values.max() if valid_values.size > 0 else 1.0
    min_val = valid_values.min() if valid_values.size > 0 else 0.0

    for y in range(height):
        for x in range(width):
            val = grid[y][x]
            
            # Цвет клетки
            if val == -1.0:
                color = (0, 0, 0) # Стена/Неизвестно = Черный
            elif val == 0.0:
                color = (0, 255, 0) # Цель = Ярко-зеленый
            else:
                # Градиент от Синего (близко) к Красному (далеко)
                # Нормализуем значение от 0 до 1
                ratio = (val - min_val) / (max_val - min_val + 1e-9)
                r = int(255 * ratio)
                b = int(255 * (1 - ratio))
                color = (r, 0, b)
            
            # Рисуем квадрат
            draw.rectangle(
                [x * cell_size, y * cell_size, (x + 1) * cell_size, (y + 1) * cell_size],
                fill=color, outline=(50, 50, 50)
            )
            
            # Пишем число (стоимость) в центре клетки
            if val != -1.0:
                text = f"{val:.1f}"
                # Центрируем текст (примерно)
                draw.text((x * cell_size + 5, y * cell_size + 15), text, fill=(255, 255, 255))

    img.save(filename)
    print(f"🖼️ Heatmap сохранен в {filename}")