import torch
import torch.nn.functional as F
from gpu.bfs import bfs_distance_maps

class GPUPathPlanner:
    def __init__(self, width, height, grid):
        self.width = width
        self.height = height
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else
                                   "mps" if torch.backends.mps.is_available() else "cpu")
        
        # 0 - свободно, 1 - препятствие
        # массив на C++  ---> 2D bool тензор PyTorch
        grid_tensor = torch.tensor(grid, dtype=torch.bool, device=self.device)
        self.obstacles = grid_tensor.reshape((self.height, self.width))

    def get_cost2go_windows_batch(self, agents, goals, radius):
        B = len(goals)
        side = 2 * radius + 1
        
        # Подготовка тензора целей. Формат bfs.py: [row, col] -> [y, x]
        targets_tensor = torch.tensor([[g[1], g[0]] for g in goals], dtype=torch.int64, device=self.device)
        
        # Запуск параллельного BFS
        dist_maps = bfs_distance_maps(self.obstacles, targets_tensor)
        
        # Паддинг значением -1. Обработка краев карты
        padded_maps = F.pad(dist_maps, (radius, radius, radius, radius), value=-1)
        padded_maps_cpu = padded_maps.cpu()
        
        results = []
        for i in range(B):
            ax, ay = agents[i]
            
            # Окна, с учетом паддинга
            win = padded_maps_cpu[i, ay : ay + side, ax : ax + side]
            
            # Конвертация в формат C++ реализации (float и -1.0 для недостижимых)
            win_float = win.to(torch.float32)
            win_float[win == -1] = -1.0
            
            results.append(win_float.tolist())
            
        return results