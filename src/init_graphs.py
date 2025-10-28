import numpy as np
import copy
from state_class import State

def legalize(input_bitwidth, cell_map, min_map):
    min_map = copy.deepcopy(cell_map)
    for i in range(input_bitwidth):
        min_map[i, 0] = 0
        min_map[i, i] = 0
    for x in range(input_bitwidth-1, 0, -1):
        last_y = x
        for y in range(x-1, -1, -1):
            if cell_map[x, y] == 1:
                cell_map[last_y-1, y] = 1
                min_map[last_y-1, y] = 0
                last_y = y
    return cell_map, min_map

def get_sklansky_cell_map(n: int):
    cell_map = np.zeros((n, n))
    level_map = np.zeros((n, n))
    for i in range(n):
        cell_map[i, i] = 1
        level_map[i, i] = 1
        t = i
        now = i
        x = 1
        level = 1
        while t > 0:
            if t % 2 ==1:
                last_now = now
                now -= x
                cell_map[i, now] = 1
                level_map[i, now] = max(level, level_map[last_now-1, now]) +1
                level += 1
            t = t // 2
            x *= 2
    
    min_map = copy.deepcopy(cell_map)
    for i in range(n):
        min_map[i, i] = 0
        min_map[i, 0] = 0
    
    level = level_map.max()
    size = cell_map.sum() - n
    cell_map, min_map = legalize(n, cell_map, min_map)
    return cell_map, min_map

def get_sklansky_init(n: int):
    cell_map = np.zeros((n, n))
    level_map = np.zeros((n, n))
    for i in range(n):
        cell_map[i, i] = 1
        level_map[i, i] = 1
        t = i
        now = i
        x = 1
        level = 1
        while t > 0:
            if t % 2 ==1:
                last_now = now
                now -= x
                cell_map[i, now] = 1
                level_map[i, now] = max(level, level_map[last_now-1, now]) +1
                level += 1
            t = t // 2
            x *= 2
    
    min_map = copy.deepcopy(cell_map)
    for i in range(n):
        min_map[i, i] = 0
        min_map[i, 0] = 0
    
    level = level_map.max()
    size = cell_map.sum() - n
    state = State(n, level, size, cell_map, level_map, min_map,
            0, 0, 0, 0)
    state.cell_map, state.min_map = state.legalize(cell_map, min_map)
    state.update_available_choice()
    return state

def get_normal_cell_map(n: int):
    cell_map = np.zeros((n, n))
    level_map = np.zeros((n, n))
    for i in range(n):
        cell_map[i, i] = 1
        cell_map[i, 0] = 1
        level_map[i, i] = 1
        level_map[i, 0] = i+1
    level = level_map.max()
    min_map = copy.deepcopy(cell_map)
    for i in range(n):
        min_map[i, i] = 0
        min_map[i, 0] = 0
    size = cell_map.sum() - n
    
    return cell_map, min_map

def get_normal_init(n: int):
    cell_map = np.zeros((n, n))
    level_map = np.zeros((n, n))
    for i in range(n):
        cell_map[i, i] = 1
        cell_map[i, 0] = 1
        level_map[i, i] = 1
        level_map[i, 0] = i+1
    level = level_map.max()
    min_map = copy.deepcopy(cell_map)
    for i in range(n):
        min_map[i, i] = 0
        min_map[i, 0] = 0
    size = cell_map.sum() - n
    state = State(n, level, size, cell_map, level_map, min_map,
            0, 0, 0, 0)
    return state

def get_brent_kung_cell_map(n: int):

    def update_level_map(cell_map, level_map):
        level_map.fill(0)
        level_map[0, 0] = 1
        for x in range(1, n):
            level_map[x, x] = 1
            last_y = x
            for y in range(x-1, -1, -1):
                if cell_map[x, y] == 1:
                    level_map[x, y] = max(level_map[x, last_y], level_map[last_y-1, y])+ 1
                    last_y = y
        return level_map

    cell_map = np.zeros((n, n))
    level_map = np.zeros((n, n))
    for i in range(n):
        cell_map[i, i] = 1 
        cell_map[i, 0] = 1
    t = 2
    while t < n:
        for i in range(t-1, n, t):
            cell_map[i, i-t+1] = 1
        t *= 2
    level_map = update_level_map(cell_map, level_map)
    level = level_map.max()
    min_map = copy.deepcopy(cell_map)
    for i in range(n):
        min_map[i, i] = 0
        min_map[i, 0] = 0
    size = cell_map.sum() - n
    print("BK level ={}, size = {}".format(level_map.max(), cell_map.sum()-n))
    return cell_map, min_map

def get_brent_kung_init(n: int):

    def update_level_map(cell_map, level_map):
        level_map.fill(0)
        level_map[0, 0] = 1
        for x in range(1, n):
            level_map[x, x] = 1
            last_y = x
            for y in range(x-1, -1, -1):
                if cell_map[x, y] == 1:
                    level_map[x, y] = max(level_map[x, last_y], level_map[last_y-1, y])+ 1
                    last_y = y
        return level_map

    cell_map = np.zeros((n, n))
    level_map = np.zeros((n, n))
    for i in range(n):
        cell_map[i, i] = 1 
        cell_map[i, 0] = 1
    t = 2
    while t < n:
        for i in range(t-1, n, t):
            cell_map[i, i-t+1] = 1
        t *= 2
    level_map = update_level_map(cell_map, level_map)
    level = level_map.max()
    min_map = copy.deepcopy(cell_map)
    for i in range(n):
        min_map[i, i] = 0
        min_map[i, 0] = 0
    size = cell_map.sum() - n
    print("BK level ={}, size = {}".format(level_map.max(), cell_map.sum()-n))
    state = State(n, level, size, cell_map, level_map, min_map,
            0, 0, 0, 0)
    return state