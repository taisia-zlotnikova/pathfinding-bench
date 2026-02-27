#!/bin/bash

# 1. Останавливаем скрипт при ошибке
set -e

echo "=== Начало установки зависимостей и сборки проекта ==="

# 2. Проверка системных зависимостей (CMake и компилятор)
if ! command -v cmake &> /dev/null; then
    echo "❌ Ошибка: CMake не найден. Установите его (sudo apt install cmake / brew install cmake)"
    exit 1
fi

if ! command -v make &> /dev/null; then
    echo "❌ Ошибка: Make не найден."
    exit 1
fi

# 3. Создаем виртуальное окружение Python (рекомендуется)
if [ ! -d "pathfinding_env" ]; then
    echo "🐍 Создаем виртуальное окружение (pathfinding_env)..."
    python3 -m venv pathfinding_env
fi

# 4. Активируем окружение и ставим зависимости
echo "📦 Устанавливаем Python-зависимости..."
source pathfinding_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Сборка C++ проекта
echo "🔨 Сборка C++ ядра..."
# Удаляем старую папку build для чистой сборки (опционально)
rm -rf build
mkdir build
cd build

# Запуск CMake
# python3 -m pybind11 --cmakedir помогает CMake найти pybind11 внутри pathfinding_env
cmake -DCMAKE_PREFIX_PATH=$(python3 -m pybind11 --cmakedir) ..
make

echo "✅ Установка завершена!"
echo "👉 Чтобы начать работу, активируйте окружение: source pathfinding_env/bin/activate"
echo "👉 Читайте в README.md что можно запускать и как тестировать"