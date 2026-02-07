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