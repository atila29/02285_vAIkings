from action import ActionType, ALL_ACTIONS, UnfoldedAction, Action, Dir

from logger import log
"""
    Basic properties for agents
"""
class Agent:
    color: str  # maybe enums?
    id_: str
    row: int
    col: int

    def __init__(self, id_, color, row, col):
        self.row = row
        self.col = col
        self.color = color
        self.id_ = id_

    def __repr__(self):
        return self.color + " Agent with letter " + self.id_

    def __str__(self):
        return self.id_

