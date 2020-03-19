from typing import Tuple
from level_element import LevelElement

class Agent(LevelElement):

    color: str # maybe enums?
    name: str
    position = Tuple[int, int]

    def __init__(self, name, color):
        self.color = color
        self.name = name


