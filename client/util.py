from action import Dir

def reverse_direction(direction):
    if direction == Dir.N:
        return Dir.S
    elif direction == Dir.S:
        return Dir.N
    elif direction == Dir.E:
        return Dir.W
    else:
        return Dir.E

def is_adjacent(pos1, pos2):
    for dir in [Dir.N, Dir.S, Dir.E, Dir.W]:
        if pos1[0] + dir.d_row == pos2[0] and pos1[1] + dir.d_col == pos2[1]:
            return True
    return False