from typing import Tuple

class Agent:

    color: str # maybe enums?
    name: str
    row = -1
    col = -1

    def __init__(self, name: str, color: str, row: int, col: int):
        self.color = color
        self.name = name
        self.row = row
        self.col = col


