import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

def plot_metrics(csv_file):
    if not os.path.exists(csv_file):
        print(f"Файл {csv_file} не найден. Сначала запустите collect_metrics.py")
        return

    df = pd.read_csv(csv_file)
    
    # Оставляем только успешные запуски
    df = df[df["Success"] == True]

    # Создаем папку для графиков
    output_dir = "results/plots"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Настройка стиля
    sns.set_theme(style="whitegrid")
    
    # 1. Сравнение ВРЕМЕНИ работы (Time)
    plt.figure(figsize=(10, 6))
    sns.boxplot(x="Algorithm", y="Time (ms)", data=df, showfliers=False) # showfliers=False скрывает выбросы
    plt.title("Сравнение времени работы (меньше - лучше)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/time_comparison.png")
    print(f"📈 График времени сохранен в {output_dir}/time_comparison.png")

    # 2. Сравнение раскрытых узлов (Expanded Nodes)
    plt.figure(figsize=(10, 6))
    sns.boxplot(x="Algorithm", y="Expanded Nodes", data=df, showfliers=False)
    plt.title("Количество раскрытых вершин (меньше - лучше)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/nodes_comparison.png")
    print(f"📈 График узлов сохранен в {output_dir}/nodes_comparison.png")

    # 3. Сравнение субоптимальности (WA*)
    # Фильтруем только те, где suboptimality > 0 (обычно WA*)
    plt.figure(figsize=(10, 6))
    sns.barplot(x="Algorithm", y="Suboptimality (%)", data=df, errorbar=None)
    plt.title("Насколько путь длиннее оптимального (%)")
    plt.xticks(rotation=45)
    plt.ylabel("Перерасход пути (%)")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/suboptimality.png")
    print(f"📈 График оптимальности сохранен в {output_dir}/suboptimality.png")

if __name__ == "__main__":
    # Укажите путь к вашему CSV
    csv_path = "results/benchmark_results.csv" 
    plot_metrics(csv_path)