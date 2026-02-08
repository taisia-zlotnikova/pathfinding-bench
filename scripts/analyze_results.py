import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(os.path.dirname(BASE_DIR), 'results')

def plot_time_comparison(df, output_dir):
    """График 1: Время работы (Barplot)"""
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    
    # Считаем среднее
    summary = df.groupby(['Algorithm', 'Connectivity'])['TimeMS'].mean().reset_index()
    
    sns.barplot(data=summary, x='Algorithm', y='TimeMS', hue='Connectivity')
    plt.title('Сравнение времени работы (меньше = лучше)')
    plt.ylabel('Время (мс)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    save_path = os.path.join(output_dir, '1_time_comparison.png')
    plt.savefig(save_path)
    plt.close()
    print(f"   📊 Сохранен график времени: {save_path}")

def plot_nodes_comparison(df, output_dir):
    """График 2: Раскрытые вершины (Log Scale Barplot)"""
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    
    summary = df.groupby(['Algorithm', 'Connectivity'])['ExpandedNodes'].mean().reset_index()
    
    sns.barplot(data=summary, x='Algorithm', y='ExpandedNodes', hue='Connectivity')
    plt.title('Количество раскрытых вершин (Log Scale, меньше = лучше)')
    plt.ylabel('Вершины (log)')
    plt.yscale('log') # Важно для сравнения Dijkstra и A*
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    save_path = os.path.join(output_dir, '2_nodes_comparison.png')
    plt.savefig(save_path)
    plt.close()
    print(f"   📊 Сохранен график вершин: {save_path}")

def plot_tradeoff(df, output_dir):
    """График 3: Компромисс Скорость vs Точность (Dual Axis)"""
    # Для этого графика берем только 8-связную сетку и алгоритмы A*/WA*
    target_df = df[
        (df['Connectivity'] == 8) & 
        (df['Algorithm'].str.contains('A\*|WA\*'))
    ]
    
    if target_df.empty:
        return

    summary = target_df.groupby('Algorithm').agg({
        'TimeMS': 'mean',
        'Suboptimality': 'mean'
    }).reset_index().sort_values('TimeMS', ascending=False)

    fig, ax1 = plt.subplots(figsize=(10, 6))
    sns.set_style("white")

    # Столбцы - Время
    sns.barplot(data=summary, x='Algorithm', y='TimeMS', ax=ax1, color='#3498db', alpha=0.6)
    ax1.set_ylabel('Время (мс)', color='#2980b9', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='#2980b9')
    ax1.set_title('Trade-off: Скорость vs Ошибка (8-связность)', fontsize=14)

    # Линия - Ошибка
    ax2 = ax1.twinx()
    sns.lineplot(data=summary, x='Algorithm', y='Suboptimality', ax=ax2, color='#e74c3c', marker='o', linewidth=3)
    ax2.set_ylabel('Субоптимальность (%)', color='#c0392b', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='#c0392b')
    ax2.set_ylim(bottom=-0.1)

    # Подписи значений
    for i in range(summary.shape[0]):
        val = summary['Suboptimality'].iloc[i]
        ax2.text(i, val + 0.1, f'{val:.2f}%', color='#c0392b', ha='center', fontweight='bold')

    plt.tight_layout()
    save_path = os.path.join(output_dir, '3_tradeoff.png')
    plt.savefig(save_path)
    plt.close()
    print(f"   📊 Сохранен график компромисса: {save_path}")

def analyze_all_folders():
    print(f"🔍 Поиск результатов в: {RESULTS_DIR}")
    
    # Ищем все подпапки в results
    subdirs = [d for d in os.listdir(RESULTS_DIR) if os.path.isdir(os.path.join(RESULTS_DIR, d))]
    
    for subdir in subdirs:
        folder_path = os.path.join(RESULTS_DIR, subdir)
        
        # Ищем CSV файл в этой папке (берем самый свежий)
        csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
        if not csv_files:
            continue
            
        csv_files.sort(reverse=True) # Самый новый первый
        latest_csv = csv_files[0]
        
        print(f"\n📂 Обработка папки: {subdir.upper()}")
        print(f"   📄 Файл данных: {os.path.basename(latest_csv)}")
        
        try:
            df = pd.read_csv(latest_csv)
            # Оставляем только успешные попытки
            df = df[df['Success'] == True]
            
            if df.empty:
                print("   ⚠️ В файле нет успешных путей.")
                continue

            # Генерация 3-х графиков
            plot_time_comparison(df, folder_path)
            plot_nodes_comparison(df, folder_path)
            plot_tradeoff(df, folder_path)
            
        except Exception as e:
            print(f"   ❌ Ошибка обработки: {e}")

if __name__ == "__main__":
    analyze_all_folders()