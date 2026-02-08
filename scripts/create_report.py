import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import argparse
import glob
import numpy as np

# --- НАСТРОЙКА ВИЗУАЛА ---
# Используем профессиональную, чистую тему
sns.set_theme(style="whitegrid", context="paper", font_scale=1.3)
colors = sns.color_palette("deep")

def load_data(files):
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f)
            # Фикс для старых файлов
            if "Connectivity" not in df.columns: df["Connectivity"] = 8
            dfs.append(df)
        except Exception as e:
            print(f"❌ Ошибка чтения {f}: {e}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

# ==========================================
# НОВЫЕ "НОРМАЛЬНЫЕ" ГРАФИКИ
# ==========================================

def plot_1_tradeoff_scatter(df):
    """
    График 1: Точечная диаграмма компромисса (Скорость vs Качество).
    Идеальный алгоритм должен быть в левом нижнем углу.
    """
    # Берем только алгоритмы с эвристикой Octile для честного сравнения
    subset = df[df["Heuristic"] == "Octile"].copy()
    
    plt.figure(figsize=(10, 7))
    
    # Рисуем точки
    sns.scatterplot(
        data=subset,
        x="Time (ms)",
        y="Suboptimality (%)",
        hue="Algorithm",    # Разные цвета для A* и WA*
        style="Connectivity", # Разные маркеры для 4 и 8 связности
        s=100,              # Размер точек
        alpha=0.7,
        palette="deep"
    )

    # Добавляем "Зону идеала"
    plt.axhline(y=0, color='green', linestyle='--', alpha=0.3)
    plt.text(subset["Time (ms)"].min(), 0.5, "Оптимальные пути (A*)", color='green', va='bottom')

    plt.title("Компромисс: Скорость поиска против Качества пути", fontweight='bold')
    plt.xlabel("Время выполнения (мс) → (меньше = быстрее)")
    plt.ylabel("Субоптимальность (%) → (меньше = лучше)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    plt.savefig("results/plots/1_tradeoff_scatter.png", dpi=150, bbox_inches='tight')
    plt.close()


def plot_2_heuristics_bar(df):
    """
    График 2: Столбчатая диаграмма эффективности эвристик.
    Исключаем Дейкстру, чтобы не ломать масштаб. Сравниваем только A*.
    """
    # Фильтруем: только A* и только 4-связность (классический лабиринт)
    subset = df[
        (df["Algorithm"].str.startswith("A*")) & 
        (df["Connectivity"] == 4)
    ].copy()
    
    plt.figure(figsize=(10, 6))
    
    # Столбчатая диаграмма со средним значением и доверительным интервалом (усы)
    ax = sns.barplot(
        data=subset,
        x="Heuristic",
        y="Expanded Nodes",
        palette="viridis",
        capsize=.1, # Добавляем "шляпки" на усы ошибок
        err_kws={'linewidth': 2}
    )
    
    # Добавляем значения над столбцами
    for container in ax.containers:
        ax.bar_label(container, fmt='%.0f', padding=3)

    plt.title("Какая эвристика эффективнее? (Сравнение на 4-связном графе)", fontweight='bold')
    plt.ylabel("Среднее кол-во раскрытых узлов (меньше = лучше)")
    plt.xlabel("Тип эвристики")
    plt.tight_layout()
    plt.savefig("results/plots/2_heuristics_bar.png", dpi=150)
    plt.close()


def plot_3_connectivity_box(df):
    """
    График 3: Парный ящик с усами. Как связность влияет на длину пути.
    """
    # Берем только A* с Octile, чтобы сравнить влияние именно связности
    subset = df[
        (df["Algorithm"] == "A* (Octile)") | 
        (df["Algorithm"] == "Dijkstra") # Можно добавить Дейкстру для фона
    ].copy()
    
    plt.figure(figsize=(9, 7))

    sns.boxplot(
        data=subset,
        x="Connectivity",
        y="Path Length",
        hue="Algorithm", # Сравниваем внутри каждой связности
        palette="Set2",
        linewidth=2,
        showfliers=False # Скрываем экстремальные выбросы для чистоты
    )
    
    # Добавляем точки поверх, чтобы видеть реальное распределение (если данных немного)
    sns.stripplot(
        data=subset,
        x="Connectivity",
        y="Path Length",
        hue="Algorithm",
        dodge=True, 
        alpha=0.3, 
        palette='dark:black',
        legend=False
    )

    plt.title("Влияние 8-связности на длину пути", fontweight='bold')
    plt.ylabel("Геометрическая длина пути")
    plt.xlabel("Связность графа (количество соседей)")
    plt.legend(title="Алгоритм")
    plt.tight_layout()
    plt.savefig("results/plots/3_connectivity_box.png", dpi=150)
    plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Генерация НОРМАЛЬНЫХ отчетов.")
    parser.add_argument("files", nargs="*", help="CSV файлы. Если пусто - все в results/")
    args = parser.parse_args()

    os.makedirs("results/plots", exist_ok=True)

    files = args.files if args.files else glob.glob("results/*.csv")
    if not files:
        print("❌ Нет данных в results/*.csv")
        exit()
        
    print(f"📂 Загружаю {len(files)} файлов...")
    df = load_data(files)

    if df.empty:
        print("❌ Данные пусты.")
        exit()

    print("📊 Строю График 1: Компромисс (Scatter)...")
    plot_1_tradeoff_scatter(df)
    
    print("📊 Строю График 2: Эвристики (Bar)...")
    plot_2_heuristics_bar(df)
    
    print("📊 Строю График 3: Связность (Box)...")
    plot_3_connectivity_box(df)

    print("\n✅ Готово! Смотри нормальные графики в папке results/plots/")