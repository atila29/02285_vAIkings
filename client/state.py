from typing import List
from enum import Enum
from agent import Agent
from box import Box
from level_element import LevelElement

class State(object):
    level = List[List[LevelElement]]
    agents = List[Agent]
    boxes = List[Box]

    def __init__(self):
        self.agents = []
        self.boxes = []
        self.level = []

    # TODO: impl.
    def __repr__(self):
        pass