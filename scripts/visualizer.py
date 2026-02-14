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