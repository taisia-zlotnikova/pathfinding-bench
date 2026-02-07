#include "PathPlanner.h"

PathPlanner::PathPlanner(int width, int height, const std::vector<int>& grid)
    : width_(width), height_(height), grid_(grid) {}

double PathPlanner::calculateHeuristic(int idx1, int idx2, HeuristicType type) {
  if (type == HeuristicType::Zero) return 0.0;

  auto [x1, y1] = toCoord(idx1);
  auto [x2, y2] = toCoord(idx2);
  double dx = std::abs(x1 - x2);
  double dy = std::abs(y1 - y2);

  // [cite: 15, 16, 17]
  switch (type) {
    case HeuristicType::Manhattan:
      return dx + dy;
    case HeuristicType::Euclidean:
      return std::sqrt(dx * dx + dy * dy);
    case HeuristicType::Octile:
      return (dx + dy) + (std::sqrt(2) - 2) * std::min(dx, dy);
    default:
      return 0.0;
  }
}

// Пока реализуем базовые 4 соседа, 8-связность и corner cutting добавим в Этапе
// 3
std::vector<int> PathPlanner::getNeighbors(int current_id, int connectivity) {
  std::vector<int> neighbors;
  auto [cx, cy] = toCoord(current_id);

  // 1. Ортогональные перемещения (Up, Down, Left, Right)
  // Порядок: Right, Down, Left, Up
  int dx_orth[] = {1, 0, -1, 0};
  int dy_orth[] = {0, 1, 0, -1};

  // Сохраним доступность ортогональных соседей для проверки диагоналей
  // free_orth[0] -> Right, free_orth[1] -> Down, etc.
  bool free_orth[4] = {false, false, false, false};

  for (int i = 0; i < 4; ++i) {
    int nx = cx + dx_orth[i];
    int ny = cy + dy_orth[i];

    if (nx >= 0 && nx < width_ && ny >= 0 && ny < height_) {
      int n_idx = toIndex(nx, ny);
      if (grid_[n_idx] == 0) {
        neighbors.push_back(n_idx);
        free_orth[i] = true;  // Запоминаем, что здесь проход свободен
      }
    }
  }

  // 2. Диагональные перемещения (только если connectivity == 8)
  if (connectivity == 8) {
    // Направления диагоналей соответствуют комбинациям ортогональных:
    // 0: Right-Down (+1, +1) -> нужны Orth[0] (Right) и Orth[1] (Down)
    // 1: Left-Down  (-1, +1) -> нужны Orth[2] (Left)  и Orth[1] (Down)
    // 2: Left-Up    (-1, -1) -> нужны Orth[2] (Left)  и Orth[3] (Up)
    // 3: Right-Up   (+1, -1) -> нужны Orth[0] (Right) и Orth[3] (Up)

    int dx_diag[] = {1, -1, -1, 1};
    int dy_diag[] = {1, 1, -1, -1};

    // Индексы ортогональных соседей, которые должны быть свободны
    int check1[] = {0, 2, 2, 0};  // Right, Left, Left, Right
    int check2[] = {1, 1, 3, 3};  // Down, Down, Up, Up

    for (int i = 0; i < 4; ++i) {
      int nx = cx + dx_diag[i];
      int ny = cy + dy_diag[i];

      if (nx >= 0 && nx < width_ && ny >= 0 && ny < height_) {
        int n_idx = toIndex(nx, ny);

        // Главное условие: сама диагональная клетка свободна
        if (grid_[n_idx] == 0) {
          // Проверка Corner Cutting:
          // Разрешено только если ОБА ортогональных соседа свободны
          if (free_orth[check1[i]] && free_orth[check2[i]]) {
            neighbors.push_back(n_idx);
          }
        }
      }
    }
  }

  return neighbors;
}

SearchResult PathPlanner::findPath(int start_x, int start_y, int goal_x,
                                   int goal_y, AlgorithmType algo,
                                   HeuristicType heuristic, double weight,
                                   int connectivity) {
  int start_id = toIndex(start_x, start_y);
  int goal_id = toIndex(goal_x, goal_y);

  // Проверка границ
  if (start_x < 0 || start_x >= width_ || start_y < 0 || start_y >= height_ ||
      goal_x < 0 || goal_x >= width_ || goal_y < 0 || goal_y >= height_) {
    return {{}, false, 0, 0.0, 0.0};
  }

  if (algo == AlgorithmType::BFS) {
    return runBFS(start_id, goal_id, connectivity);
  } else {
    // Dijkstra - это A* с h=0 [cite: 8]
    if (algo == AlgorithmType::Dijkstra) {
      heuristic = HeuristicType::Zero;
      weight = 0.0;
    }
    return runAStarLike(start_id, goal_id, heuristic, weight, connectivity);
  }
}

SearchResult PathPlanner::runBFS(int start_id, int goal_id, int connectivity) {
  auto start_time = std::chrono::high_resolution_clock::now();

  std::queue<int> q;
  q.push(start_id);

  std::unordered_map<int, int> came_from;
  std::unordered_map<int, double> dist_so_far;  // Нужно для длины пути
  came_from[start_id] = -1;
  dist_so_far[start_id] = 0.0;

  int expanded_nodes = 0;
  bool found = false;

  while (!q.empty()) {
    int current = q.front();
    q.pop();
    expanded_nodes++;  // [cite: 47]

    if (current == goal_id) {
      found = true;
      break;
    }

    for (int next : getNeighbors(current, connectivity)) {
      if (came_from.find(next) == came_from.end()) {
        came_from[next] = current;
        // В BFS на гриде вес ребра всегда 1.0 (для 4-связности)
        // Для 8-связности BFS не гарантирует кратчайший путь, если есть
        // диагонали sqrt(2) Но реализуем классический BFS по графу
        dist_so_far[next] = dist_so_far[current] + 1.0;
        q.push(next);
      }
    }
  }

  // Реконструкция пути
  std::vector<std::pair<int, int>> path;
  if (found) {
    int curr = goal_id;
    while (curr != -1) {
      path.push_back(toCoord(curr));
      curr = came_from[curr];
    }
    std::reverse(path.begin(), path.end());
  }

  auto end_time = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> duration = end_time - start_time;

  return {path, found, expanded_nodes, found ? dist_so_far[goal_id] : 0.0,
          duration.count()};
}

SearchResult PathPlanner::runAStarLike(int start_id, int goal_id,
                                       HeuristicType h_type, double weight,
                                       int connectivity) {
  auto start_time = std::chrono::high_resolution_clock::now();

  std::priority_queue<Node, std::vector<Node>, std::greater<Node>> open_set;
  open_set.push({start_id, 0.0, 0.0});

  std::unordered_map<int, int> came_from;
  std::unordered_map<int, double> cost_so_far;

  came_from[start_id] = -1;
  cost_so_far[start_id] = 0.0;

  int expanded_nodes = 0;
  bool found = false;

  while (!open_set.empty()) {
    Node current = open_set.top();
    open_set.pop();

    // Lazy deletion: если нашли путь лучше к этому узлу ранее, пропускаем
    // старую запись
    if (current.g_score > cost_so_far[current.id] + 1e-9) continue;

    expanded_nodes++;

    if (current.id == goal_id) {
      found = true;
      break;
    }

    for (int next : getNeighbors(current.id, connectivity)) {
      // Получаем координаты текущей и следующей клетки для проверки типа хода
      auto [cx, cy] = toCoord(current.id);
      auto [nx, ny] = toCoord(next);

      double move_cost;

      // Если изменились обе координаты (и x, и y), значит ход диагональный
      if (cx != nx && cy != ny) {
        move_cost = std::sqrt(2.0);  // ~1.414
      } else {
        move_cost = 1.0;
      }

      double new_cost = cost_so_far[current.id] + move_cost;

      if (cost_so_far.find(next) == cost_so_far.end() ||
          new_cost < cost_so_far[next]) {
        cost_so_far[next] = new_cost;
        double priority =
            new_cost + weight * calculateHeuristic(next, goal_id, h_type);
        came_from[next] = current.id;
        open_set.push({next, priority, new_cost});
      }
    }
  }

  // Реконструкция пути
  std::vector<std::pair<int, int>> path;
  if (found) {
    int curr = goal_id;
    while (curr != -1) {
      path.push_back(toCoord(curr));
      curr = came_from[curr];
    }
    std::reverse(path.begin(), path.end());
  }

  auto end_time = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> duration = end_time - start_time;

  return {path, found, expanded_nodes, found ? cost_so_far[goal_id] : 0.0,
          duration.count()};
}