from typing import Tuple

class Agent(object):

    color: str # maybe enums?
    name: str
    position = Tuple[int, int]

    def __init__(self, color):
        self.color = color
        self.name = name


