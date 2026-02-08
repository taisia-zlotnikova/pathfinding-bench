import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(os.path.dirname(BASE_DIR), 'results')

def get_plot_title(base_title, df, file_tag):
    """Генерирует умный заголовок: если в данных 1 карта, пишет её имя."""
    unique_maps = df['MapName'].unique()
    if len(unique_maps) == 1:
        return f"{base_title}: {unique_maps[0]}"
    else:
        return f"{base_title} ({file_tag})"

def plot_time_comparison(df, output_dir, file_tag):
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    summary = df.groupby(['Algorithm', 'Connectivity'])['TimeMS'].mean().reset_index()
    sns.barplot(data=summary, x='Algorithm', y='TimeMS', hue='Connectivity')
    
    plt.title(get_plot_title('Время работы', df, file_tag))
    plt.ylabel('Время (мс)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{file_tag}_time.png'))
    plt.close()

def plot_nodes_comparison(df, output_dir, file_tag):
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    summary = df.groupby(['Algorithm', 'Connectivity'])['ExpandedNodes'].mean().reset_index()
    sns.barplot(data=summary, x='Algorithm', y='ExpandedNodes', hue='Connectivity')
    
    plt.title(get_plot_title('Раскрытые вершины', df, file_tag))
    plt.ylabel('Вершины (log)')
    plt.yscale('log')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{file_tag}_nodes.png'))
    plt.close()

def plot_tradeoff(df, output_dir, file_tag):
    target_df = df[
        (df['Connectivity'] == 8) & 
        (df['Algorithm'].str.contains('A\*|WA\*'))
    ]
    if target_df.empty: return

    summary = target_df.groupby('Algorithm').agg({
        'TimeMS': 'mean', 'Suboptimality': 'mean'
    }).reset_index().sort_values('TimeMS', ascending=False)

    algo_order = summary['Algorithm'].tolist()
    fig, ax1 = plt.subplots(figsize=(11, 7))
    sns.set_style("white")

    # ВРЕМЯ
    sns.barplot(data=summary, x='Algorithm', y='TimeMS', ax=ax1, 
                order=algo_order, color='#85C1E9', alpha=0.8, edgecolor='black')
    ax1.set_ylabel('Время (мс)', color='#2E86C1', fontsize=12, fontweight='bold')
    
    title = get_plot_title('Trade-off', df, file_tag)
    ax1.set_title(title, fontsize=14, fontweight='bold')
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
    plt.savefig(os.path.join(output_dir, f'{file_tag}_tradeoff.png'), dpi=150)
    plt.close()

def analyze_recursive():
    print(f"🔍 Сканирование папки: {RESULTS_DIR}")
    if not os.path.exists(RESULTS_DIR): return

    for root, dirs, files in os.walk(RESULTS_DIR):
        csv_files = [f for f in files if f.endswith('.csv') and f.startswith('res_')]
        
        for csv_file in csv_files:
            csv_path = os.path.join(root, csv_file)
            file_tag = os.path.splitext(csv_file)[0]
            
            # Если графики уже есть, можно пропустить (раскомментируйте, если нужно)
            if os.path.exists(os.path.join(root, f'{file_tag}_tradeoff.png')): continue

            try:
                df = pd.read_csv(csv_path)
                df = df[df['Success'] == True]
                if df.empty: continue
                
                print(f"📊 Строим графики для: {csv_file}")
                plot_time_comparison(df, root, file_tag)
                plot_nodes_comparison(df, root, file_tag)
                plot_tradeoff(df, root, file_tag)
                
            except Exception as e:
                print(f"❌ Ошибка {csv_file}: {e}")

if __name__ == "__main__":
    analyze_recursive()