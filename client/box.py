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

    def __repr__(self):
        return self.color + " Box with letter " + self.name
        

    def __str__(self):
        return self.name
