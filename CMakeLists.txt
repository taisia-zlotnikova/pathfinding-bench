cmake_minimum_required(VERSION 3.10)
project(PathFindingCore)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Пытаемся найти pybind11 (предполагается, что он установлен через pip install pybind11)
# Или можно использовать execute_process для поиска пути
execute_process(
    COMMAND python3 -m pybind11 --includes
    OUTPUT_VARIABLE PYBIND11_INCLUDES
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Если pybind11 не найден через includes, пробуем стандартный find_package
find_package(pybind11 CONFIG)

if(NOT pybind11_FOUND)
    # Fallback: Если пакет не найден, можно подключить его как submodule (опционально)
    # Но для начала предполагаем, что пользователь установил его в окружении
    message(STATUS "Pybind11 config not found, using python includes via manual flags might be needed if compilation fails.")
endif()

# Создаем модуль
pybind11_add_module(pathfinding_core
    src/bindings.cpp
    src/PathPlanner.cpp
)

target_include_directories(pathfinding_core PRIVATE src)