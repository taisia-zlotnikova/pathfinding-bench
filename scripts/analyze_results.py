import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(os.path.dirname(BASE_DIR), 'results')

def plot_time_comparison(df, output_dir, file_tag):
    """График 1: Время работы"""
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    summary = df.groupby(['Algorithm', 'Connectivity'])['TimeMS'].mean().reset_index()
    sns.barplot(data=summary, x='Algorithm', y='TimeMS', hue='Connectivity')
    plt.title(f'Время работы (Источник: {file_tag})')
    plt.ylabel('Время (мс)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Имя файла теперь содержит имя исходного CSV, чтобы не перезаписывать
    save_path = os.path.join(output_dir, f'{file_tag}_time.png')
    plt.savefig(save_path)
    plt.close()

def plot_nodes_comparison(df, output_dir, file_tag):
    """График 2: Раскрытые вершины"""
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    summary = df.groupby(['Algorithm', 'Connectivity'])['ExpandedNodes'].mean().reset_index()
    sns.barplot(data=summary, x='Algorithm', y='ExpandedNodes', hue='Connectivity')
    plt.title(f'Раскрытые вершины (Источник: {file_tag})')
    plt.ylabel('Вершины (log)')
    plt.yscale('log')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    save_path = os.path.join(output_dir, f'{file_tag}_nodes.png')
    plt.savefig(save_path)
    plt.close()

def plot_tradeoff(df, output_dir, file_tag):
    """График 3: Trade-off"""
    target_df = df[
        (df['Connectivity'] == 8) & 
        (df['Algorithm'].str.contains('A\*|WA\*'))
    ]
    if target_df.empty: return

    summary = target_df.groupby('Algorithm').agg({
        'TimeMS': 'mean',
        'Suboptimality': 'mean'
    }).reset_index().sort_values('TimeMS', ascending=False)

    algo_order = summary['Algorithm'].tolist()
    fig, ax1 = plt.subplots(figsize=(11, 7))
    sns.set_style("white")

    # ВРЕМЯ
    sns.barplot(data=summary, x='Algorithm', y='TimeMS', ax=ax1, 
                order=algo_order, color='#85C1E9', alpha=0.8, edgecolor='black')
    ax1.set_ylabel('Время (мс)', color='#2E86C1', fontsize=12, fontweight='bold')
    ax1.set_title(f'Trade-off (Источник: {file_tag})', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    # ОШИБКА
    ax2 = ax1.twinx()
    sns.pointplot(data=summary, x='Algorithm', y='Suboptimality', ax=ax2, 
                  order=algo_order, color='#C0392B', markers='o', 
                  linewidth=3, markersize=10)
    ax2.set_ylabel('Субоптимальность (%)', color='#C0392B', fontsize=12, fontweight='bold')
    ax2.grid(False)

    max_subopt = summary['Suboptimality'].max()
    y_limit_top = 1.0 if max_subopt < 1.0 else max_subopt * 1.3
    ax2.set_ylim(bottom=-y_limit_top * 0.1, top=y_limit_top)
    
    text_offset = y_limit_top * 0.05
    for i in range(summary.shape[0]):
        val = summary['Suboptimality'].iloc[i]
        ax2.text(i, val + text_offset, f'{val:.2f}%', color='#C0392B', 
                 ha='center', va='bottom', fontweight='bold', fontsize=10)

    plt.tight_layout()
    save_path = os.path.join(output_dir, f'{file_tag}_tradeoff.png')
    plt.savefig(save_path, dpi=150)
    plt.close()

def analyze_recursive():
    print(f"🔍 Сканирование папки: {RESULTS_DIR}")
    if not os.path.exists(RESULTS_DIR):
        print("❌ Папка results не найдена.")
        return

    # Проходим по всем подпапкам
    for root, dirs, files in os.walk(RESULTS_DIR):
        # Находим ВСЕ csv файлы в текущей папке
        csv_files = [f for f in files if f.endswith('.csv') and f.startswith('res_')]
        
        if csv_files:
            print(f"\n📂 Папка: {os.path.relpath(root, RESULTS_DIR)}")
            
            # --- ИЗМЕНЕНИЕ: Обрабатываем КАЖДЫЙ файл, а не только последний ---
            for csv_file in csv_files:
                csv_path = os.path.join(root, csv_file)
                
                # Создаем короткое имя для файла (без расширения .csv)
                # Например: res_maze_uniform_100_20231027_1200
                file_tag = os.path.splitext(csv_file)[0]
                
                # Проверяем, есть ли уже графики для этого файла, чтобы не перерисовывать зря?
                # (Можно закомментировать это условие, если хочешь всегда перерисовывать)
                if os.path.exists(os.path.join(root, f'{file_tag}_tradeoff.png')):
                    print(f"   ⏩ Пропуск (графики уже есть): {csv_file}")
                    continue

                print(f"   📊 Обработка: {csv_file}")
                try:
                    df = pd.read_csv(csv_path)
                    df = df[df['Success'] == True]
                    
                    if df.empty:
                        print("      ⚠️ Нет успешных путей.")
                        continue

                    # Передаем file_tag, чтобы имя картинки было уникальным
                    plot_time_comparison(df, root, file_tag)
                    plot_nodes_comparison(df, root, file_tag)
                    plot_tradeoff(df, root, file_tag)
                    
                except Exception as e:
                    print(f"      ❌ Ошибка: {e}")

if __name__ == "__main__":
    analyze_recursive()