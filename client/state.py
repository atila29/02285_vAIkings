import sys
from typing import List, Tuple, Dict
from enum import Enum
from agent import Agent
from box import Box
from level import LevelElement, Level
import copy

LEVEL = Level()

"""
    Custom object that keeps track of the non-static information about the level
    i.e. the position of boxes and agents
"""
class State(object):
    agents = Dict[Tuple[int, int], Agent]
    boxes = Dict[Tuple[int, int], Box]


    def __init__(self):
        self.agents = {}
        self.boxes = {}

    # TODO: impl.
    def __repr__(self):
        return str((self.agents, self.boxes))

    def __str__(self):
        return self.__repr__()

    def print_current_state(self):
        level_copy = copy.deepcopy(LEVEL.level)
        for pos in self.agents:
            level_copy[pos[0]][pos[1]] = self.agents[pos]
        for pos in self.boxes:
            level_copy[pos[0]][pos[1]] = self.boxes[pos]

        lines =[]
        for row in level_copy:
            line  =[]
            for elm in row:
                line.append(str(elm))
            lines.append(''.join(line))
        print("\n".join(lines), file=sys.stderr, flush=True)