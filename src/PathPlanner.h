#pragma once
#include <algorithm>
#include <chrono>
#include <cmath>
#include <iostream>
#include <queue>
#include <unordered_map>
#include <vector>

// Типы алгоритмов
enum class AlgorithmType { BFS, Dijkstra, AStar, WAStar };

// Типы эвристик
enum class HeuristicType {
  Manhattan,
  Euclidean,
  Octile,
  Zero  // Для Dijkstra
};

// Структура результата
struct SearchResult {
  std::vector<std::pair<int, int>> path;
  bool found;
  int expanded_nodes;
  double path_length;
  double execution_time;
};

// Узел графа для Priority Queue
struct Node {
  int id;  // y * width + x
  double f_score;
  double g_score;

  // Для priority_queue (меньший f_score имеет приоритет)
  bool operator>(const Node& other) const { return f_score > other.f_score; }
};

class PathPlanner {
 public:
  PathPlanner(int width, int height, const std::vector<int>& grid);

  // Основной метод поиска
  SearchResult findPath(int start_x, int start_y, int goal_x, int goal_y,
                        AlgorithmType algo,
                        HeuristicType heuristic = HeuristicType::Manhattan,
                        double weight = 1.0, int connectivity = 4);

 private:
  int width_, height_;
  std::vector<int> grid_;  // 0 - свободно, 1 - препятствие

  // Вспомогательные методы
  double calculateHeuristic(int idx1, int idx2, HeuristicType type);
  std::vector<int> getNeighbors(int current_id, int connectivity);
  SearchResult runAStarLike(int start_id, int goal_id, HeuristicType h_type,
                            double weight, int connectivity);
  SearchResult runBFS(int start_id, int goal_id, int connectivity);

  // Преобразование координат
  int toIndex(int x, int y) const { return y * width_ + x; }
  std::pair<int, int> toCoord(int index) const {
    return {index % width_, index / width_};
  }
};