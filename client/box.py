from typing import Tuple

class Box(object):

    color: str # maybe enums?
    name: str
    position = Tuple[int, int]

    def __init__(self, name, color):
        self.color = color
        self.name = name


