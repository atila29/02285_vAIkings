from typing import List
from enum import Enum
from agent import Agent
from box import Box
from level import LevelElement, Level

LEVEL = Level()

"""
    Custom object that keeps track of the non-static information about the level
    i.e. the position of boxes and agents
"""
class State(object):
    agents = List[Agent]
    boxes = List[Box]


    def __init__(self):
        self.agents = []
        self.boxes = []

    # TODO: impl.
    def __repr__(self):
        pass