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