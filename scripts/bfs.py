import torch


def bfs_distance_map(obstacles: torch.Tensor, target: torch.Tensor, max_steps: int | None = None):
    """
    Single BFS distance map for a grid with obstacles.

    obstacles : bool[H, W]
    target    : int64[2]  (row, col)

    returns:
        dist : int16[H, W]
    """
    device = obstacles.device
    H, W = obstacles.shape

    dist = torch.full((H, W), -1, dtype=torch.int16, device=device)
    frontier = torch.zeros((H, W), dtype=torch.bool, device=device)
    visited = torch.zeros_like(frontier)

    r, c = target[0].item(), target[1].item()
    frontier[r, c] = True
    visited[r, c] = True
    dist[r, c] = 0

    level = 1
    if max_steps is None:
        max_steps = H * W

    while level <= max_steps:
        if not frontier.any():
            break

        next_frontier = torch.zeros_like(frontier)

        # 4-neighborhood shifts
        next_frontier[1:, :] |= frontier[:-1, :]    # up
        next_frontier[:-1, :] |= frontier[1:, :]    # down
        next_frontier[:, 1:] |= frontier[:, :-1]    # left
        next_frontier[:, :-1] |= frontier[:, 1:]    # right

        # remove visited and obstacles
        next_frontier &= ~visited
        next_frontier &= ~obstacles

        # assign distances
        dist[next_frontier] = level

        visited |= next_frontier
        frontier = next_frontier
        level += 1

    return dist


def bfs_distance_maps(obstacles: torch.Tensor,
                      targets: torch.Tensor,
                      max_steps: int | None = None):
    """
    Parallel BFS distance maps for a single grid and many targets.

    obstacles : bool[H, W]
    targets   : int64[B, 2]  (row, col)

    returns:
        dist : int16[B, H, W]
    """

    device = obstacles.device

    H, W = obstacles.shape
    B = targets.shape[0]

    # Distance tensor
    dist = torch.full(
        (B, H, W),
        -1,
        dtype=torch.int16,
        device=device
    )

    # Frontier + visited
    frontier = torch.zeros((B, H, W), dtype=torch.bool, device=device)
    visited = torch.zeros_like(frontier)

    # Initialize targets
    b_idx = torch.arange(B, device=device)

    r = targets[:, 0]
    c = targets[:, 1]

    frontier[b_idx, r, c] = True
    visited[b_idx, r, c] = True
    dist[b_idx, r, c] = 0

    level = 1

    if max_steps is None:
        max_steps = H * W

    while level <= max_steps:

        if not frontier.any():
            break

        next_frontier = torch.zeros_like(frontier)

        # shifts

        # up
        next_frontier[:, 1:, :] |= frontier[:, :-1, :]

        # down
        next_frontier[:, :-1, :] |= frontier[:, 1:, :]

        # left
        next_frontier[:, :, 1:] |= frontier[:, :, :-1]

        # right
        next_frontier[:, :, :-1] |= frontier[:, :, 1:]

        # remove visited and obstacles
        next_frontier &= ~visited
        next_frontier &= ~obstacles.unsqueeze(0)

        # assign distances
        dist[next_frontier] = level

        visited |= next_frontier
        frontier = next_frontier

        level += 1

    return dist
