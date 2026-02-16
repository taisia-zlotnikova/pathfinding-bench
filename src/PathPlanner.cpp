#include "PathPlanner.h"

#include <chrono>

PathPlanner::PathPlanner(int width, int height, const std::vector<int>& grid)
    : width_(width), height_(height), grid_(grid) {}

double PathPlanner::calculateHeuristic(int idx1, int idx2, HeuristicType type) {
  if (type == HeuristicType::Zero) return 0.0;

  int x1 = idx1 % width_;
  int y1 = idx1 / width_;
  int x2 = idx2 % width_;
  int y2 = idx2 / width_;

  double dx = std::abs(x1 - x2);
  double dy = std::abs(y1 - y2);

  // [cite: 15, 16, 17] Реализация эвристик
  switch (type) {
    case HeuristicType::Manhattan:
      return dx + dy;
    case HeuristicType::Euclidean:
      return std::sqrt(dx * dx + dy * dy);
    case HeuristicType::Octile:
      // Формула: (dx + dy) + (sqrt(2) - 2) * min(dx, dy)
      // Это математически эквивалентно max(dx, dy) + (sqrt(2)-1)*min(dx, dy)
      return (dx + dy) + (1.41421356 - 2.0) * std::min(dx, dy);
    default:
      return 0.0;
  }
}

// Оптимизированное получение соседей без лишних аллокаций
void PathPlanner::getNeighbors(int current_id, int connectivity,
                               std::vector<int>& out_neighbors,
                               std::vector<double>& out_costs) {
  out_neighbors.clear();
  out_costs.clear();

  int cx = current_id % width_;
  int cy = current_id / width_;

  // Ортогональные сдвиги: Right, Down, Left, Up
  const int dx_orth[] = {1, 0, -1, 0};
  const int dy_orth[] = {0, 1, 0, -1};
  bool free_orth[4] = {false, false, false, false};

  // 1. Проверяем ортогональных соседей [cite: 21]
  for (int i = 0; i < 4; ++i) {
    int nx = cx + dx_orth[i];
    int ny = cy + dy_orth[i];

    if (nx >= 0 && nx < width_ && ny >= 0 && ny < height_) {
      int n_idx = ny * width_ + nx;
      if (grid_[n_idx] == 0) {
        out_neighbors.push_back(n_idx);
        out_costs.push_back(1.0);
        free_orth[i] = true;
      }
    }
  }

  // 2. Диагональные (только если 8-связность) [cite: 22, 23]
  if (connectivity == 8) {
    const int dx_diag[] = {1, -1, -1, 1};
    const int dy_diag[] = {1, 1, -1, -1};
    const double diag_cost = 1.41421356;  // sqrt(2)

    // Для проверки Corner Cutting: диагональ разрешена, если оба ортогональных
    // соседа свободны Индексы в free_orth: 0=Right, 1=Down, 2=Left, 3=Up Diag 0
    // (Right-Down): нужны Right(0) и Down(1) Diag 1 (Left-Down):  нужны Left(2)
    // и Down(1) Diag 2 (Left-Up):    нужны Left(2)  и Up(3) Diag 3 (Right-Up):
    // нужны Right(0) и Up(3)
    const int check1[] = {0, 2, 2, 0};
    const int check2[] = {1, 1, 3, 3};

    for (int i = 0; i < 4; ++i) {
      int nx = cx + dx_diag[i];
      int ny = cy + dy_diag[i];

      if (nx >= 0 && nx < width_ && ny >= 0 && ny < height_) {
        int n_idx = ny * width_ + nx;
        if (grid_[n_idx] == 0) {
          // Corner Cutting check
          if (free_orth[check1[i]] && free_orth[check2[i]]) {
            out_neighbors.push_back(n_idx);
            out_costs.push_back(diag_cost);
          }
        }
      }
    }
  }
}

std::vector<std::vector<double>> PathPlanner::getCost2GoWindow(
    int agent_x, int agent_y, int goal_x, int goal_y, int radius,
    int connectivity) {
  // Размер окна
  int side = 2 * radius + 1;
  // Инициализируем окно значением -1.0 (обозначает препятствие или
  // недостижимость)
  std::vector<std::vector<double>> window(side,
                                          std::vector<double>(side, -1.0));

  // Проверка координат
  if (goal_x < 0 || goal_x >= width_ || goal_y < 0 || goal_y >= height_ ||
      grid_[toIndex(goal_x, goal_y)] != 0) {
    return window;  // Цель недостижима или некорректна
  }

  // Определяем границы окна в глобальных координатах
  int win_min_x = agent_x - radius;
  int win_max_x = agent_x + radius;
  int win_min_y = agent_y - radius;
  int win_max_y = agent_y + radius;

  // Подсчитываем, сколько клеток внутри окна теоретически проходимы.
  // Это нужно для ранней остановки Dijkstra.
  int valid_targets_in_window = 0;
  for (int wy = 0; wy < side; ++wy) {
    for (int wx = 0; wx < side; ++wx) {
      int gx = win_min_x + wx;
      int gy = win_min_y + wy;
      if (gx >= 0 && gx < width_ && gy >= 0 && gy < height_) {
        if (grid_[toIndex(gx, gy)] == 0) {
          valid_targets_in_window++;
        }
      }
    }
  }

  if (valid_targets_in_window == 0) return window;

  // Запускаем Dijkstra ОТ ЦЕЛИ (Reverse Dijkstra)
  int goal_id = toIndex(goal_x, goal_y);

  std::priority_queue<Node, std::vector<Node>, std::greater<Node>> open_set;
  open_set.push({goal_id, 0.0, 0.0});  // f_score = distance

  const double INF = std::numeric_limits<double>::infinity();
  std::vector<double> dist_matrix(width_ * height_, INF);
  dist_matrix[goal_id] = 0.0;

  std::vector<int> neighbors;
  std::vector<double> costs;
  neighbors.reserve(8);
  costs.reserve(8);

  int found_in_window_count = 0;

  while (!open_set.empty()) {
    Node current = open_set.top();
    open_set.pop();

    if (current.f_score > dist_matrix[current.id] + 1e-9) continue;

    // Координаты текущей клетки
    auto [cx, cy] = toCoord(current.id);

    // Если текущая клетка попадает в окно агента, записываем результат
    if (cx >= win_min_x && cx <= win_max_x && cy >= win_min_y &&
        cy <= win_max_y) {
      // Преобразуем глобальные в локальные окна
      int local_x = cx - win_min_x;
      int local_y = cy - win_min_y;

      // Если мы еще не записывали сюда значение
      if (window[local_y][local_x] == -1.0) {
        window[local_y][local_x] = current.f_score;
        found_in_window_count++;
      }
    }

    // Если мы нашли значения для всех свободных клеток окна, можно завершать
    if (found_in_window_count >= valid_targets_in_window) {
      break;
    }

    getNeighbors(current.id, connectivity, neighbors, costs);

    for (size_t i = 0; i < neighbors.size(); ++i) {
      int next = neighbors[i];
      double move_cost = costs[i];
      double new_dist = dist_matrix[current.id] + move_cost;

      if (new_dist < dist_matrix[next]) {
        dist_matrix[next] = new_dist;
        open_set.push({next, new_dist, new_dist});
      }
    }
  }

  return window;
}

SearchResult PathPlanner::findPath(int start_x, int start_y, int goal_x,
                                   int goal_y, AlgorithmType algo,
                                   HeuristicType heuristic, double weight,
                                   int connectivity) {
  // Валидация координат
  if (start_x < 0 || start_x >= width_ || start_y < 0 || start_y >= height_ ||
      goal_x < 0 || goal_x >= width_ || goal_y < 0 || goal_y >= height_) {
    return {{}, false, 0, 0.0, 0.0};
  }

  int start_id = toIndex(start_x, start_y);
  int goal_id = toIndex(goal_x, goal_y);

  // Если старт или цель в препятствии — пути нет
  if (grid_[start_id] != 0 ||
      grid_[grid_.size() > (size_t)goal_id ? goal_id : 0] != 0) {
    // Доп. проверка границ массива на всякий случай, хотя start_id проверен
    // выше
    if (grid_[start_id] != 0 || grid_[goal_id] != 0)
      return {{}, false, 0, 0.0, 0.0};
  }

  if (algo == AlgorithmType::BFS) {
    return runBFS(start_id, goal_id, connectivity);
  } else {
    // Dijkstra это частный случай A* с h=0
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

  std::vector<int> came_from(width_ * height_, -1);
  std::vector<bool> visited(width_ * height_, false);

  visited[start_id] = true;

  int expanded_nodes = 0;
  bool found = false;

  // Предварительное выделение памяти для соседей
  std::vector<int> neighbors;
  std::vector<double> costs;
  neighbors.reserve(8);
  costs.reserve(8);

  while (!q.empty()) {
    int current = q.front();
    q.pop();
    expanded_nodes++;

    if (current == goal_id) {
      found = true;
      break;
    }

    getNeighbors(current, connectivity, neighbors, costs);

    for (int next : neighbors) {
      if (!visited[next]) {
        visited[next] = true;
        came_from[next] = current;
        q.push(next);
      }
    }
  }

  // Реконструкция пути
  std::vector<std::pair<int, int>> path;
  double true_length = 0.0;

  if (found) {
    int curr = goal_id;
    while (curr != start_id) {
      path.push_back(toCoord(curr));
      int prev = came_from[curr];

      // Считаем точную длину для метрики (даже если BFS искал по ребрам)
      int cx = curr % width_;
      int cy = curr / width_;
      int px = prev % width_;
      int py = prev / width_;

      if (cx != px && cy != py)
        true_length += 1.41421356;
      else
        true_length += 1.0;

      curr = prev;
    }
    path.push_back(toCoord(start_id));
    std::reverse(path.begin(), path.end());
  }

  auto end_time = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> duration = end_time - start_time;

  return {path, found, expanded_nodes, true_length, duration.count()};
}

SearchResult PathPlanner::runAStarLike(int start_id, int goal_id,
                                       HeuristicType h_type, double weight,
                                       int connectivity) {
  auto start_time = std::chrono::high_resolution_clock::now();

  // Min-heap priority queue
  std::priority_queue<Node, std::vector<Node>, std::greater<Node>> open_set;

  double h_start = calculateHeuristic(start_id, goal_id, h_type);
  open_set.push({start_id, weight * h_start, 0.0});

  const double INF = std::numeric_limits<double>::infinity();
  std::vector<double> cost_so_far(width_ * height_, INF);
  std::vector<int> came_from(width_ * height_, -1);

  cost_so_far[start_id] = 0.0;

  int expanded_nodes = 0;
  bool found = false;

  std::vector<int> neighbors;
  std::vector<double> costs;
  neighbors.reserve(8);
  costs.reserve(8);

  while (!open_set.empty()) {
    Node current = open_set.top();
    open_set.pop();

    // Lazy deletion: если извлеченный путь хуже уже известного, пропускаем
    if (current.g_score > cost_so_far[current.id] + 1e-9) continue;

    if (current.id == goal_id) {
      found = true;
      break;
    }

    expanded_nodes++;

    getNeighbors(current.id, connectivity, neighbors, costs);

    for (size_t i = 0; i < neighbors.size(); ++i) {
      int next = neighbors[i];
      double move_cost = costs[i];
      double new_g = cost_so_far[current.id] + move_cost;

      if (new_g < cost_so_far[next]) {
        cost_so_far[next] = new_g;
        double h = calculateHeuristic(next, goal_id, h_type);
        // f = g + w*h
        double new_f = new_g + weight * h;

        came_from[next] = current.id;
        open_set.push({next, new_f, new_g});
      }
    }
  }

  // Реконструкция
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