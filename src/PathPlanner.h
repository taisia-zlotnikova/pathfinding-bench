#pragma once
#include <algorithm>
#include <cmath>
#include <iostream>
#include <limits>
#include <queue>
#include <vector>

// Типы алгоритмов
enum class AlgorithmType { BFS, Dijkstra, AStar, WAStar };

// Типы эвристик
enum class HeuristicType { Manhattan, Euclidean, Octile, Zero };

// Структура результата
struct SearchResult {
  std::vector<std::pair<int, int>> path;
  bool found;
  int expanded_nodes;
  double path_length;
  double execution_time;
};

// Узел для Priority Queue
struct Node {
  int id;
  double f_score;
  double g_score;  // Вернули g_score для корректной проверки lazy deletion

  // Priority Queue в C++ по умолчанию max-heap, поэтому для min-heap (меньший f
  // лучше) оператор должен возвращать true, если текущий элемент "больше"
  // (имеет меньший приоритет)
  bool operator>(const Node& other) const {
    // Если f_score равны, можно сравнивать g_score для тай-брейкинга
    // (опционально)
    return f_score > other.f_score;
  }
};

class PathPlanner {
 public:
  PathPlanner(int width, int height, const std::vector<int>& grid);

  SearchResult findPath(int start_x, int start_y, int goal_x, int goal_y,
                        AlgorithmType algo,
                        HeuristicType heuristic = HeuristicType::Manhattan,
                        double weight = 1.0, int connectivity = 4);

 private:
  int width_, height_;
  const std::vector<int>& grid_;  // Ссылка, чтобы не копировать память

  // Хелперы
  double calculateHeuristic(int idx1, int idx2, HeuristicType type);

  // Передаем векторы по ссылке, чтобы избежать re-allocation в цикле
  void getNeighbors(int current_id, int connectivity,
                    std::vector<int>& out_neighbors,
                    std::vector<double>& out_costs);

  SearchResult runAStarLike(int start_id, int goal_id, HeuristicType h_type,
                            double weight, int connectivity);
  SearchResult runBFS(int start_id, int goal_id, int connectivity);

  inline int toIndex(int x, int y) const { return y * width_ + x; }
  inline std::pair<int, int> toCoord(int index) const {
    return {index % width_, index / width_};
  }
};