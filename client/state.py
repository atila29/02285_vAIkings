import sys
from typing import List, Tuple, Dict
from enum import Enum
from box import Box
from level import LevelElement, Level, Wall, AgentElement
import copy

LEVEL = Level()

"""
    Custom object that keeps track of the non-static information about the level
    i.e. the position of boxes and agents
"""
class State(object):
    agents = Dict[Tuple[int, int], AgentElement]
    boxes = Dict[Tuple[int, int], Box]
    g: int
    parent: 'State'
    unfolded_action: 'UnfoldedAction'

    def __init__(self, copy_state: 'State' = None):

        if copy_state is None:
            self.agents = {}
            self.boxes = {}
            self.g = 0
            self.parent = None
            self.unfolded_action = None
        else:
            self.agents = copy.deepcopy(copy_state.agents)
            self.boxes = copy.deepcopy(copy_state.boxes)
            self.g = copy_state.g + 1
            self.parent = copy_state
            self.unfolded_action = copy_state.unfolded_action

        

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

    def is_free(self, row , col) -> 'bool':
        #print('index: ' + str((row, col)), file=sys.stderr, flush=True)

        if (row, col) in self.agents or (row, col) in self.boxes or isinstance(LEVEL.level[row][col], Wall):
            return False
        return True
        
    def is_initial_state(self) -> 'bool':
        return self.parent is None
    
