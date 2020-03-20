from typing import Tuple


class Box:

    color: str # maybe enums?
    name: str
    row = -1
    col = -1

    def __init__(self, name, color, row, col):
        self.color = color
        self.name = name
        self.row = row
        self.col = col

