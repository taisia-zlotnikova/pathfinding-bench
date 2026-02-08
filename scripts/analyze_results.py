# # import pandas as pd
# # import matplotlib.pyplot as plt
# # import seaborn as sns
# # import os
# # import sys

# # # Путь к результатам
# # BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# # RESULTS_DIR = os.path.join(os.path.dirname(BASE_DIR), 'results')

# # def get_latest_csv():
# #     if not os.path.exists(RESULTS_DIR):
# #         print("Папка results не найдена.")
# #         return None
# #     files = [f for f in os.listdir(RESULTS_DIR) if f.endswith('.csv')]
# #     if not files:
# #         print("CSV файлы не найдены.")
# #         return None
# #     files.sort(reverse=True)
# #     return os.path.join(RESULTS_DIR, files[0])

# # def analyze():
# #     csv_file = get_latest_csv()
# #     if not csv_file: return

# #     print(f"📊 Анализ файла: {csv_file}")
# #     df = pd.read_csv(csv_file)
    
# #     # Фильтруем только найденные пути
# #     df_success = df[df['Success'] == True]

# #     # Создаем папку для графиков
# #     plots_dir = os.path.join(RESULTS_DIR, 'plots')
# #     os.makedirs(plots_dir, exist_ok=True)

# #     # ==========================================
# #     # 1. ТАБЛИЦА: СРЕДНЕЕ ВРЕМЯ И УЗЛЫ ПО АЛГОРИТМАМ
# #     # ==========================================
# #     print("\n--- 📈 Средние показатели по алгоритмам (все карты) ---")
# #     summary = df_success.groupby(['Algorithm', 'Connectivity'])[['TimeMS', 'ExpandedNodes', 'PathLength']].mean().reset_index()
# #     print(summary.to_string())

# #     # ==========================================
# #     # 2. ГРАФИК: ВРЕМЯ РАБОТЫ (Time vs Algorithm)
# #     # ==========================================
# #     plt.figure(figsize=(12, 6))
# #     sns.barplot(data=df_success, x='Algorithm', y='TimeMS', hue='Connectivity', errorbar=None)
# #     plt.title('Среднее время выполнения (меньше = лучше)')
# #     plt.ylabel('Время (мс)')
# #     plt.xticks(rotation=45)
# #     plt.tight_layout()
# #     plt.savefig(os.path.join(plots_dir, 'time_comparison.png'))
# #     print(f"Сохранен график: {plots_dir}/time_comparison.png")

# #     # ==========================================
# #     # 3. ГРАФИК: РАСКРЫТЫЕ ВЕРШИНЫ (Nodes vs Algorithm)
# #     # ==========================================
# #     plt.figure(figsize=(12, 6))
# #     # Используем логарифмическую шкалу, так как Dijkstra может раскрыть ОЧЕНЬ много
# #     sns.barplot(data=df_success, x='Algorithm', y='ExpandedNodes', hue='Connectivity', errorbar=None)
# #     plt.title('Раскрытые вершины (меньше = лучше)')
# #     plt.yscale('log')
# #     plt.ylabel('Кол-во вершин (Log Scale)')
# #     plt.xticks(rotation=45)
# #     plt.tight_layout()
# #     plt.savefig(os.path.join(plots_dir, 'nodes_comparison.png'))
# #     print(f"Сохранен график: {plots_dir}/nodes_comparison.png")

# #     # ==========================================
# #     # 4. СРАВНЕНИЕ A* vs WA* (Suboptimality)
# #     # ==========================================
# #     # Берем только WA* алгоритмы
# #     wa_df = df_success[df_success['Algorithm'].str.contains('WA*')]
# #     if not wa_df.empty:
# #         plt.figure(figsize=(10, 6))
# #         sns.boxplot(data=wa_df, x='Algorithm', y='Suboptimality')
# #         plt.title('Субоптимальность WA* (насколько путь длиннее идеального)')
# #         plt.ylabel('Превышение длины (%)')
# #         plt.tight_layout()
# #         plt.savefig(os.path.join(plots_dir, 'suboptimality.png'))
# #         print(f"Сохранен график: {plots_dir}/suboptimality.png")

# #     # ==========================================
# #     # 5. ТЕКСТОВЫЕ ВЫВОДЫ (Эмуляция отчета)
# #     # ==========================================
# #     print("\n=== 📝 АВТОМАТИЧЕСКИЕ ВЫВОДЫ ===")
    
# #     # Сравниваем Dijkstra vs A* (Octile)
# #     dijkstra = df_success[df_success['Algorithm'] == 'Dijkstra']['ExpandedNodes'].mean()
# #     astar = df_success[df_success['Algorithm'] == 'A* (Octile)']['ExpandedNodes'].mean()
    
# #     if dijkstra and astar:
# #         ratio = dijkstra / astar
# #         print(f"1. Эвристика работает: A* раскрывает в {ratio:.1f} раз меньше вершин, чем Dijkstra.")

# #     # Сравниваем A* vs WA*
# #     astar_time = df_success[df_success['Algorithm'] == 'A* (Octile)']['TimeMS'].mean()
# #     wastar_time = df_success[df_success['Algorithm'] == 'WA* (x1.5)']['TimeMS'].mean()
    
# #     if astar_time and wastar_time:
# #         speedup = astar_time / wastar_time
# #         print(f"2. WA* (x1.5) быстрее обычного A* в {speedup:.1f} раз(а).")

# #     print("3. Влияние связности: 8-связные пути обычно короче, но требуют проверки большего числа соседей.")

# # if __name__ == "__main__":
# #     analyze()
# import pandas as pd
# import matplotlib.pyplot as plt
# import seaborn as sns
# import os
# import sys

# # Настройки путей
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# RESULTS_DIR = os.path.join(os.path.dirname(BASE_DIR), 'results')
# PLOTS_DIR = os.path.join(RESULTS_DIR, 'plots')

# def get_latest_csv():
#     if not os.path.exists(RESULTS_DIR): return None
#     files = [f for f in os.listdir(RESULTS_DIR) if f.endswith('.csv')]
#     if not files: return None
#     files.sort(reverse=True)
#     return os.path.join(RESULTS_DIR, files[0])

# def plot_tradeoff_graph(df):
#     """
#     Строит график компромисса: Время vs Точность.
#     Показывает, как сильно мы ускоряемся (Time) и чем за это платим (Suboptimality).
#     """
#     # Фильтруем только A* и WA* для сравнения
#     target_algos = df[df['Algorithm'].str.contains('A\*|WA\*')]
    
#     # Группируем, чтобы получить средние значения
#     # Берем только 8-связную сетку для чистоты эксперимента (или можно усреднить всё)
#     df_8 = target_algos[target_algos['Connectivity'] == 8]
#     if df_8.empty:
#         df_8 = target_algos # Если нет 8-связных, берем все
        
#     summary = df_8.groupby('Algorithm').agg({
#         'TimeMS': 'mean',
#         'Suboptimality': 'mean'
#     }).reset_index()

#     # Сортируем по времени (от медленного A* к быстрому WA*)
#     summary = summary.sort_values('TimeMS', ascending=False)

#     # --- ПОСТРОЕНИЕ ГРАФИКА ---
#     fig, ax1 = plt.subplots(figsize=(12, 7))
#     sns.set_style("whitegrid")

#     # 1. Столбцы - ВРЕМЯ (Левая ось Y)
#     bar_plot = sns.barplot(data=summary, x='Algorithm', y='TimeMS', ax=ax1, 
#                            alpha=0.6, color='#2ecc71', edgecolor='black')
#     ax1.set_ylabel('Среднее время (мс)', color='green', fontsize=12)
#     ax1.tick_params(axis='y', labelcolor='green')
#     ax1.set_xlabel('Алгоритм', fontsize=12)
#     ax1.set_title('Компромисс: Скорость vs Точность (на 8-связной сетке)', fontsize=14, fontweight='bold')

#     # Добавляем значения над столбцами
#     for p in bar_plot.patches:
#         ax1.annotate(f'{p.get_height():.1f} ms', 
#                      (p.get_x() + p.get_width() / 2., p.get_height()), 
#                      ha = 'center', va = 'center', xytext = (0, 9), 
#                      textcoords = 'offset points', color='green', fontsize=10, fontweight='bold')

#     # 2. Линия - ОШИБКА (Правая ось Y)
#     ax2 = ax1.twinx()
#     line_plot = sns.lineplot(data=summary, x='Algorithm', y='Suboptimality', ax=ax2, 
#                              color='#e74c3c', marker='o', linewidth=3, markersize=10)
#     ax2.set_ylabel('Субоптимальность (% превышения длины)', color='red', fontsize=12)
#     ax2.tick_params(axis='y', labelcolor='red')
#     ax2.set_ylim(bottom=-0.5) # Чуть ниже нуля, чтобы A* не прилипал к оси

#     # Добавляем значения над точками линии
#     for i in range(summary.shape[0]):
#         val = summary['Suboptimality'].iloc[i]
#         ax2.text(i, val + 0.2, f'{val:.2f}%', color='red', ha='center', fontweight='bold')

#     plt.tight_layout()
#     output_path = os.path.join(PLOTS_DIR, 'tradeoff_analysis.png')
#     plt.savefig(output_path, dpi=300)
#     print(f"✅ График сохранен: {output_path}")

# def analyze():
#     csv_file = get_latest_csv()
#     if not csv_file:
#         print("❌ CSV файл с результатами не найден. Сначала запустите run_experiments.py")
#         return

#     print(f"📊 Чтение данных: {csv_file}")
#     df = pd.read_csv(csv_file)
    
#     # Только успешные попытки
#     df = df[df['Success'] == True]
    
#     os.makedirs(PLOTS_DIR, exist_ok=True)

#     # 1. Основной график trade-off
#     plot_tradeoff_graph(df)

#     # 2. Текстовая сводка для отчета
#     print("\n=== 📝 СВОДКА ДЛЯ ОТЧЕТА (Сравнение A* и WA*) ===")
    
#     astar_row = df[df['Algorithm'] == 'A* (Octile)']['TimeMS'].mean()
#     if pd.isna(astar_row): 
#         # Если вдруг нет Octile, пробуем просто A*
#         astar_row = df[df['Algorithm'].str.startswith('A*')]['TimeMS'].mean()

#     # Сравнение с WA* 1.5
#     wa_row_time = df[df['Algorithm'] == 'WA* (x1.5)']['TimeMS'].mean()
#     wa_row_err = df[df['Algorithm'] == 'WA* (x1.5)']['Suboptimality'].mean()

#     if astar_row and wa_row_time:
#         speedup = astar_row / wa_row_time
#         print(f"🚀 Ускорение WA*(1.5) относительно A*: в {speedup:.2f} раз(а)")
#         print(f"📉 Плата за скорость: путь длиннее всего на {wa_row_err:.2f}%")
#         print("Вывод: WA* (1.5) дает огромное преимущество в скорости при ничтожной потере качества.")

# if __name__ == "__main__":
#     analyze()

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Настройки путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(os.path.dirname(BASE_DIR), 'results')
PLOTS_DIR = os.path.join(RESULTS_DIR, 'plots')

def get_latest_csv():
    if not os.path.exists(RESULTS_DIR): return None
    files = [f for f in os.listdir(RESULTS_DIR) if f.endswith('.csv')]
    if not files: return None
    files.sort(reverse=True)
    return os.path.join(RESULTS_DIR, files[0])

def plot_tradeoff_for_maptype(df, map_type):
    """
    Строит график Trade-off (Время vs Точность) для конкретного типа карты.
    """
    print(f"   🎨 Рисуем график для типа: {map_type}...")
    
    # Фильтруем алгоритмы A* и WA*
    target_algos = df[df['Algorithm'].str.contains('A\*|WA\*')]
    
    # Берем 8-связную сетку (она показательнее для субоптимальности)
    # Если данных нет, берем что есть
    df_8 = target_algos[target_algos['Connectivity'] == 8]
    if df_8.empty:
        df_8 = target_algos 

    if df_8.empty:
        print(f"      ⚠️ Нет данных для {map_type} (A*/WA*). Пропуск.")
        return

    summary = df_8.groupby('Algorithm').agg({
        'TimeMS': 'mean',
        'Suboptimality': 'mean'
    }).reset_index()

    # Сортировка по времени
    summary = summary.sort_values('TimeMS', ascending=False)

    # --- ГРАФИК ---
    fig, ax1 = plt.subplots(figsize=(10, 6))
    sns.set_style("whitegrid")

    # Столбцы - ВРЕМЯ
    bar_plot = sns.barplot(data=summary, x='Algorithm', y='TimeMS', ax=ax1, 
                           alpha=0.6, color='#3498db', edgecolor='black') # Синий цвет
    ax1.set_ylabel('Время (мс)', color='#2980b9', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='#2980b9')
    ax1.set_xlabel('Алгоритм', fontsize=12)
    
    # Заголовок с типом карты
    ax1.set_title(f'Тип карты: {map_type.upper()} | Скорость vs Точность', fontsize=14, fontweight='bold')

    # Значения над столбцами
    max_y = summary['TimeMS'].max()
    for p in bar_plot.patches:
        height = p.get_height()
        ax1.annotate(f'{height:.1f}', 
                     (p.get_x() + p.get_width() / 2., height), 
                     ha='center', va='bottom', color='black', fontsize=9, xytext=(0, 2), textcoords='offset points')

    # Линия - ОШИБКА
    ax2 = ax1.twinx()
    sns.lineplot(data=summary, x='Algorithm', y='Suboptimality', ax=ax2, 
                 color='#e74c3c', marker='o', linewidth=3, markersize=8) # Красный цвет
    ax2.set_ylabel('Субоптимальность (%)', color='#c0392b', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='#c0392b')
    ax2.set_ylim(bottom=-0.1) # Чтобы линия не упиралась в пол

    # Значения над точками
    for i in range(summary.shape[0]):
        val = summary['Suboptimality'].iloc[i]
        # Смещаем текст чуть выше точки
        ax2.text(i, val + (val * 0.1 if val > 0 else 0.05), f'{val:.2f}%', 
                 color='#c0392b', ha='center', fontweight='bold', fontsize=10)

    plt.tight_layout()
    
    # Сохраняем с уникальным именем
    filename = f'tradeoff_{map_type}.png'
    output_path = os.path.join(PLOTS_DIR, filename)
    plt.savefig(output_path, dpi=150)
    plt.close() # Закрываем фигуру, чтобы освободить память

def analyze():
    csv_file = get_latest_csv()
    if not csv_file:
        print("❌ CSV файл не найден.")
        return

    print(f"📊 Чтение данных: {csv_file}")
    df = pd.read_csv(csv_file)
    df = df[df['Success'] == True] # Только успешные пути
    
    os.makedirs(PLOTS_DIR, exist_ok=True)

    # 1. Получаем список уникальных типов карт, которые были в тесте
    if 'MapType' not in df.columns:
        print("❌ В CSV нет колонки MapType. Перезапустите run_experiments.py")
        return

    map_types = df['MapType'].unique()
    print(f"🔍 Найдены типы карт: {map_types}")

    # 2. Цикл по типам карт
    for m_type in map_types:
        # Берем подмножество данных только для этого типа
        subset = df[df['MapType'] == m_type]
        plot_tradeoff_for_maptype(subset, m_type)

    print(f"\n✅ Готово! Графики сохранены в {PLOTS_DIR}")

if __name__ == "__main__":
    analyze()