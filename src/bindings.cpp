#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "PathPlanner.h"

namespace py = pybind11;

PYBIND11_MODULE(pathfinding_core, m) {
  m.doc() = "Pathfinding algorithms implemented in C++ optimized";

  py::enum_<AlgorithmType>(m, "AlgorithmType")
      .value("BFS", AlgorithmType::BFS)
      .value("Dijkstra", AlgorithmType::Dijkstra)
      .value("AStar", AlgorithmType::AStar)
      .value("WAStar", AlgorithmType::WAStar)
      .export_values();

  py::enum_<HeuristicType>(m, "HeuristicType")
      .value("Manhattan", HeuristicType::Manhattan)
      .value("Euclidean", HeuristicType::Euclidean)
      .value("Octile", HeuristicType::Octile)
      .value("Zero", HeuristicType::Zero)
      .export_values();

  py::class_<SearchResult>(m, "SearchResult")
      .def_readonly("path", &SearchResult::path)
      .def_readonly("found", &SearchResult::found)
      .def_readonly("expanded_nodes", &SearchResult::expanded_nodes)
      .def_readonly("path_length", &SearchResult::path_length)
      .def_readonly("execution_time", &SearchResult::execution_time);

  py::class_<PathPlanner>(m, "PathPlanner")
      .def(py::init<int, int, const std::vector<int>&>())
      .def("find_path", &PathPlanner::findPath, py::arg("start_x"),
           py::arg("start_y"), py::arg("goal_x"), py::arg("goal_y"),
           py::arg("algo"), py::arg("heuristic") = HeuristicType::Manhattan,
           py::arg("weight") = 1.0, py::arg("connectivity") = 4)
      .def("get_cost2go_window", &PathPlanner::getCost2GoWindow,
           py::arg("agent_x"), py::arg("agent_y"), py::arg("goal_x"),
           py::arg("goal_y"), py::arg("radius"), py::arg("connectivity") = 4, 
           py::arg("fast_break") = true);
}