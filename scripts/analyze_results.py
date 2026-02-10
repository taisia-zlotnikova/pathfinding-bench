import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import argparse
import sys

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(os.path.dirname(BASE_DIR), 'results')

# --- НАСТРОЙКА ПОРЯДКА АЛГОРИТМОВ ---
ALGO_ORDER = [
    "BFS",
    "Dijkstra",
    "A* (Octile)",
    "A* (Manhattan)",
    "A* (Euclid)",
    "WA* (x1.5)",
    "WA* (x2.0)",
    "WA* (x3.0)",
    "WA* (x5.0)",
    "WA* (x10.0)",
    "Greedy"
]

def get_plot_title(base_title, df, file_tag):
    unique_maps = df['MapName'].unique()
    if len(unique_maps) == 1:
        return f"{base_title}: {unique_maps[0]}"
    else:
        return f"{base_title} ({file_tag})"

def get_order(df):
    """Сортирует алгоритмы согласно эталонному списку ALGO_ORDER."""
    present_algos = set(df['Algorithm'].unique())
    order = [algo for algo in ALGO_ORDER if algo in present_algos]
    order += list(present_algos - set(ALGO_ORDER))
    return order

def save_summary_report(df, output_dir, file_tag):
    report_path = os.path.join(output_dir, f'{file_tag}_report.txt')
    
    summary = df.groupby(['Connectivity', 'Algorithm']).agg({
        'TimeMS': 'mean',
        'ExpandedNodes': 'mean',
        'PathLength': 'mean',
        'Suboptimality': 'mean',
        'Success': 'mean'
    }).reset_index()

    summary['Algorithm'] = pd.Categorical(summary['Algorithm'], categories=ALGO_ORDER, ordered=True)
    summary = summary.sort_values(['Connectivity', 'Algorithm'])

    summary['TimeMS'] = summary['TimeMS'].round(3)
    summary['ExpandedNodes'] = summary['ExpandedNodes'].astype(int)
    summary['PathLength'] = summary['PathLength'].round(2)
    summary['Suboptimality'] = summary['Suboptimality'].round(2)
    summary['Success'] = (summary['Success'] * 100).round(1)

    text_report = []
    text_report.append(f"{'='*80}")
    text_report.append(f"📄 ОТЧЕТ: {file_tag}")
    text_report.append(f"{'='*80}\n")
    text_report.append(summary.to_string(index=False))
    text_report.append(f"\n{'='*80}")
    text_report.append("ПОЯСНЕНИЯ:")
    text_report.append("1. TimeMS: Среднее время (меньше = лучше).")
    text_report.append("2. ExpandedNodes: Раскрытые вершины (меньше = лучше).")
    text_report.append("3. Suboptimality: % отклонения от идеала (0% = идеал).")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(text_report))

# --- БАРПЛОТЫ (Усредненные) ---

def plot_time_comparison(df, output_dir, file_tag):
    plt.figure(figsize=(12, 7))
    sns.set_style("whitegrid")
    order = get_order(df)
    ax = sns.barplot(data=df, x='Algorithm', y='TimeMS', hue='Connectivity', palette="viridis", order=order)
    plt.title(get_plot_title('Время работы (Среднее)', df, file_tag))
    plt.ylabel('Время (мс)')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{file_tag}_1_time_avg.png'))
    plt.close()

def plot_nodes_comparison(df, output_dir, file_tag):
    plt.figure(figsize=(12, 7))
    sns.set_style("whitegrid")
    order = get_order(df)
    ax = sns.barplot(data=df, x='Algorithm', y='ExpandedNodes', hue='Connectivity', palette="magma", order=order)
    plt.title(get_plot_title('Раскрытые вершины (Среднее)', df, file_tag))
    plt.ylabel('Количество вершин (log scale)')
    plt.yscale('log')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{file_tag}_2_nodes_avg.png'))
    plt.close()

def plot_length_comparison(df, output_dir, file_tag):
    plt.figure(figsize=(12, 7))
    sns.set_style("whitegrid")
    order = get_order(df)
    ax = sns.barplot(data=df, x='Algorithm', y='PathLength', hue='Connectivity', palette="coolwarm", order=order)
    plt.title(get_plot_title('Длина пути (Среднее)', df, file_tag))
    plt.ylabel('Длина пути')
    min_len = df['PathLength'].min()
    max_len = df['PathLength'].max()
    if max_len > 0 and (max_len - min_len) / max_len < 0.1:
        plt.ylim(bottom=min_len * 0.95, top=max_len * 1.05)
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{file_tag}_3_length_avg.png'))
    plt.close()

def plot_tradeoff(df, output_dir, file_tag):
    conn = df['Connectivity'].max()
    target_df = df[
        (df['Connectivity'] == conn) & 
        (df['Algorithm'].str.contains('A\*|WA\*|Greedy', case=False, regex=True))
    ]
    if target_df.empty: return

    summary = target_df.groupby('Algorithm').agg({'TimeMS': 'mean', 'Suboptimality': 'mean'}).reset_index()
    present_algos = set(summary['Algorithm'])
    order = [algo for algo in ALGO_ORDER if algo in present_algos]
    summary['Algorithm'] = pd.Categorical(summary['Algorithm'], categories=order, ordered=True)
    summary = summary.sort_values('Algorithm')

    fig, ax1 = plt.subplots(figsize=(12, 7))
    sns.set_style("white")
    sns.barplot(data=summary, x='Algorithm', y='TimeMS', ax=ax1, order=order, color='#85C1E9', alpha=0.8, edgecolor='black')
    ax1.set_ylabel('Время (мс)', color='#2E86C1', fontsize=12, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='#2E86C1')
    ax1.tick_params(axis='x', rotation=45)

    ax2 = ax1.twinx()
    sns.pointplot(data=summary, x='Algorithm', y='Suboptimality', ax=ax2, order=order, color='#C0392B', markers='o', linewidth=3)
    ax2.set_ylabel('Субоптимальность (%)', color='#C0392B', fontsize=12, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='#C0392B')
    
    max_subopt = summary['Suboptimality'].max()
    y_limit_top = 1.0 if max_subopt < 1.0 else max_subopt * 1.3
    ax2.set_ylim(bottom=-0.5, top=y_limit_top)
    
    for i in range(len(summary)):
        val = summary['Suboptimality'].iloc[i]
        ax2.text(i, val + (y_limit_top*0.05), f'{val:.2f}%', color='#C0392B', ha='center', va='bottom', fontweight='bold')

    plt.title(get_plot_title(f'Trade-off (Conn={conn})', df, file_tag))
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{file_tag}_4_tradeoff.png'))
    plt.close()

# --- SCATTER PLOTS (Зависимость от сложности) ---

def plot_time_vs_length(df, output_dir, file_tag):
    unique_conns = sorted(df['Connectivity'].unique())
    n_cols = len(unique_conns)
    
    if n_cols == 0: return

    fig, axes = plt.subplots(1, n_cols, figsize=(7 * n_cols, 7), sharey=True)
    
    # Если связность одна, axes это не список, превращаем в список для унификации
    if n_cols == 1: axes = [axes]
    
    sns.set_style("whitegrid")
    
    for i, conn in enumerate(unique_conns):
        ax = axes[i] # Берем "свой" квадратик для рисования
        data = df[df['Connectivity'] == conn]
        
        # 2. Рисуем на конкретной оси ax=ax
        sns.scatterplot(
            data=data, 
            x='OptimalLength', 
            y='TimeMS', 
            hue='Algorithm', 
            style='Algorithm',
            alpha=0.7,
            palette='tab10',
            s=60,
            ax=ax, 
            legend=(i == n_cols - 1)
        )
        
        ax.set_title(f'Связность: {conn}')
        ax.set_xlabel('Оптимальная длина пути')
        
        if i == 0:
            ax.set_ylabel('Время (мс)')
        else:
            ax.set_ylabel('')

    # Выносим легенду наружу последнего графика
    if n_cols > 0:
        axes[-1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.suptitle(get_plot_title('Сложность: Время vs Длина', df, file_tag))
    plt.tight_layout()
    
    # 3. Сохраняем ОДИН раз ПОСЛЕ цикла
    plt.savefig(os.path.join(output_dir, f'{file_tag}_5_scatter_time.png'))
    plt.close()

def plot_nodes_vs_length(df, output_dir, file_tag):
    """Строит графики зависимости: Раскрытые вершины vs Длина пути (для каждой связности рядом)."""
    unique_conns = sorted(df['Connectivity'].unique())
    n_cols = len(unique_conns)
    
    if n_cols == 0: return

    fig, axes = plt.subplots(1, n_cols, figsize=(7 * n_cols, 7), sharey=True)
    
    # Если график всего один, axes не список - делаем списком
    if n_cols == 1: axes = [axes]
    
    sns.set_style("whitegrid")
    
    for i, conn in enumerate(unique_conns):
        ax = axes[i]
        data = df[df['Connectivity'] == conn]
        
        # 2. Рисуем на конкретной оси (ax=ax)
        sns.scatterplot(
            data=data, 
            x='OptimalLength', 
            y='ExpandedNodes', 
            hue='Algorithm', 
            style='Algorithm',
            alpha=0.7,
            palette='tab10',
            s=60,
            ax=ax,
            legend=(i == n_cols - 1) # Легенда только на последнем
        )
        
        ax.set_title(f'Связность: {conn}')
        ax.set_xlabel('Оптимальная длина пути')
        
        ax.set_yscale('log')
        
        if i == 0:
            ax.set_ylabel('Раскрытые вершины (log scale)')
        else:
            ax.set_ylabel('')

    # Легенда справа от последнего графика
    if n_cols > 0:
        axes[-1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.suptitle(get_plot_title('Сложность: Вершины vs Длина', df, file_tag))
    plt.tight_layout()
    
    # 3. Сохраняем один раз
    plt.savefig(os.path.join(output_dir, f'{file_tag}_6_scatter_nodes.png'))
    plt.close()
def analyze_recursive(force=False):
    print(f"🔍 Сканирование папки: {RESULTS_DIR}")
    if force:
        print("⚠️ Режим FORCE: Все графики будут пересозданы.")
        
    if not os.path.exists(RESULTS_DIR): 
        print("❌ Папка results не найдена.")
        return

    count = 0
    skipped = 0
    for root, dirs, files in os.walk(RESULTS_DIR):
        csv_files = [f for f in files if f.endswith('.csv')]
        
        for csv_file in csv_files:
            csv_path = os.path.join(root, csv_file)
            file_tag = os.path.splitext(csv_file)[0]
            
            report_path = os.path.join(root, f'{file_tag}_report.txt')
            if os.path.exists(report_path) and not force:
                print(f"⏭️  Пропуск {csv_file}")
                skipped += 1
                continue
            
            try:
                df = pd.read_csv(csv_path)
                if 'Success' not in df.columns: continue
                
                df_success = df[df['Success'] == True]

                # убрать bfs из 8-связности, так как он считает длину диагонали за 1
                df_success = df_success[~((df_success['Algorithm'] == 'BFS') & (df_success['Connectivity'] == 8))]
                if df_success.empty: continue
                
                # Генерируем 6 артефактов
                save_summary_report(df_success, root, file_tag)
                
                # Барплоты (средние значения)
                plot_time_comparison(df_success, root, file_tag)
                plot_nodes_comparison(df_success, root, file_tag)
                plot_length_comparison(df_success, root, file_tag)
                plot_tradeoff(df_success, root, file_tag)
                
                # Скаттерплоты (зависимость от длины)
                plot_time_vs_length(df_success, root, file_tag)
                plot_nodes_vs_length(df_success, root, file_tag)
                
                print(f"✅ {csv_file} -> Сохранено: отчет + 6 графиков")
                count += 1
                
            except Exception as e:
                print(f"❌ Ошибка {csv_file}: {e}")
    
    if count == 0 and skipped == 0:
        print("⚠️ CSV файлов для обработки не найдено.")
    elif count == 0 and skipped > 0:
        print(f"🏁 Готово. Обработано новых: 0. Пропущено: {skipped}. (Используйте --force для перезаписи)")
    else:
        print(f"🏁 Готово. Обработано: {count}. Пропущено: {skipped}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze Pathfinding Results")
    parser.add_argument('--force', action='store_true', help="Пересоздать все графики")
    args = parser.parse_args()
    analyze_recursive(args.force)