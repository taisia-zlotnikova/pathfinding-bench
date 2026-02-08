import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
import numpy as np

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(os.path.dirname(BASE_DIR), 'results')

def plot_time_comparison(df, output_dir):
    """График 1: Время работы"""
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    summary = df.groupby(['Algorithm', 'Connectivity'])['TimeMS'].mean().reset_index()
    sns.barplot(data=summary, x='Algorithm', y='TimeMS', hue='Connectivity')
    plt.title('Сравнение времени работы (меньше = лучше)')
    plt.ylabel('Время (мс)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '1_time_comparison.png'))
    plt.close()

def plot_nodes_comparison(df, output_dir):
    """График 2: Раскрытые вершины"""
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    summary = df.groupby(['Algorithm', 'Connectivity'])['ExpandedNodes'].mean().reset_index()
    sns.barplot(data=summary, x='Algorithm', y='ExpandedNodes', hue='Connectivity')
    plt.title('Количество раскрытых вершин (Log Scale)')
    plt.ylabel('Вершины (log)')
    plt.yscale('log')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '2_nodes_comparison.png'))
    plt.close()

def plot_tradeoff(df, output_dir):
    """График 3: Компромисс Скорость vs Точность (ИСПРАВЛЕННЫЙ)"""
    # Фильтруем данные: 8-связность и A*/WA*
    target_df = df[
        (df['Connectivity'] == 8) & 
        (df['Algorithm'].str.contains('A\*|WA\*'))
    ]
    
    if target_df.empty:
        return

    # Агрегация данных
    summary = target_df.groupby('Algorithm').agg({
        'TimeMS': 'mean',
        'Suboptimality': 'mean'
    }).reset_index().sort_values('TimeMS', ascending=False)

    algo_order = summary['Algorithm'].tolist()

    fig, ax1 = plt.subplots(figsize=(11, 7))
    sns.set_style("white") # Убираем лишнюю сетку

    # --- Ось 1: ВРЕМЯ (Столбцы) ---
    sns.barplot(data=summary, x='Algorithm', y='TimeMS', ax=ax1, 
                order=algo_order, color='#85C1E9', alpha=0.8, edgecolor='black') # Светло-синий
    
    ax1.set_ylabel('Время (мс)', color='#2E86C1', fontsize=12, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='#2E86C1')
    ax1.set_xlabel('Алгоритм', fontsize=12)
    ax1.set_title('Trade-off: Скорость vs Ошибка (8-связность)', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    # --- Ось 2: ОШИБКА (Линия) ---
    ax2 = ax1.twinx()
    sns.pointplot(data=summary, x='Algorithm', y='Suboptimality', ax=ax2, 
              order=algo_order, color='#C0392B', markers='o', 
              linewidth=3, markersize=10) # scale=1.2 заменен на linewidth и markersize
    
    ax2.set_ylabel('Субоптимальность (%)', color='#C0392B', fontsize=12, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='#C0392B')
    ax2.grid(False) # Отключаем сетку для второй оси

    # --- ИСПРАВЛЕНИЕ МАСШТАБА И ПОЗИЦИИ ТЕКСТА ---
    
    # 1. Вычисляем верхнюю границу для красной оси
    max_subopt = summary['Suboptimality'].max()
    # Если максимальная ошибка очень маленькая (например, 0), делаем искусственный "потолок", 
    # чтобы текст не улетал, а ось не схлопывалась.
    if max_subopt < 1.0: 
        y_limit_top = 1.0 # Минимум 1% шкалы, если ошибки почти нет
    else:
        y_limit_top = max_subopt * 1.3 # +30% запаса сверху

    ax2.set_ylim(bottom=-y_limit_top * 0.1, top=y_limit_top) # Небольшой отступ снизу и хороший сверху

    # 2. Динамический отступ для текста (5% от высоты графика)
    text_offset = y_limit_top * 0.05 

    # Подписи значений над красными точками
    for i in range(summary.shape[0]):
        val = summary['Suboptimality'].iloc[i]
        ax2.text(i, val + text_offset, f'{val:.2f}%', color='#C0392B', 
                 ha='center', va='bottom', fontweight='bold', fontsize=10)

    # Подписи значений над синими столбцами
    for i, p in enumerate(ax1.patches):
        height = p.get_height()
        if height > 0: # Пишем только если есть высота
            ax1.annotate(f'{height:.2f}', 
                         (p.get_x() + p.get_width() / 2., height), 
                         ha='center', va='bottom', xytext=(0, 3), 
                         textcoords='offset points', color='#2E86C1', fontsize=9)

    plt.tight_layout()
    save_path = os.path.join(output_dir, '3_tradeoff.png')
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"   📊 Сохранен график компромисса: {save_path}")

def analyze_all_folders():
    print(f"🔍 Поиск результатов в: {RESULTS_DIR}")
    if not os.path.exists(RESULTS_DIR):
        print(f"❌ Папка {RESULTS_DIR} не существует.")
        return

    subdirs = [d for d in os.listdir(RESULTS_DIR) if os.path.isdir(os.path.join(RESULTS_DIR, d))]
    
    for subdir in subdirs:
        folder_path = os.path.join(RESULTS_DIR, subdir)
        csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
        
        if not csv_files: continue
            
        csv_files.sort(reverse=True)
        latest_csv = csv_files[0]
        
        print(f"\n📂 Обработка папки: {subdir.upper()}")
        try:
            df = pd.read_csv(latest_csv)
            df = df[df['Success'] == True]
            if df.empty: continue

            plot_time_comparison(df, folder_path)
            plot_nodes_comparison(df, folder_path)
            plot_tradeoff(df, folder_path)
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    analyze_all_folders()