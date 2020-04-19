from typing import List, Dict
from strategy import StrategyBFS
from action import PULL_ACTIONS


class LevelElement:
    pass


class Wall(LevelElement):
    def __str__(self):
        return "+"


class Space(LevelElement):
    def __str__(self):
        return " "


class Goal(LevelElement):
    letter = None

    def __init__(self, letter, row, col):
        self.letter = letter
        self.row = row
        self.col = col

    def __str__(self):
        return str.lower(self.letter)


class AgentElement:
    color: str  # maybe enums?
    id_: str
    row = -1
    col = -1

    def __init__(self, id_: str, color: str, row: int, col: int):
        self.color = color
        self.id_ = id_
        self.row = row
        self.col = col

    def __repr__(self):
        return self.color + " Agent with letter " + self.id_

    def __str__(self):
        return self.id_

    def __eq__(self, other):
        return self.id_ == other.id_


class Box:
    color: str  # maybe enums?
    letter: str
    id_: str
    row = -1
    col = -1

    def __init__(self, id_, letter, color, row, col):
        self.id_ = id_
        self.color = color
        self.letter = letter
        self.row = row
        self.col = col

    def __repr__(self):
        return self.color + " Box with letter " + self.letter

    def __str__(self):
        return self.letter

    def __eq__(self, other):
        return other is not None and self.id_ == other.id_


# Class containing the static level information
class Level:
    # List containing "empty level",  i.e. walls, free space, goals
    level = List[List[LevelElement]]
    # Dictionary containing goals corresponding to different letters
    goals = Dict[str, List[Goal]]
    goals_by_pos = {}

    # Dictionary containing the deadlocks for the different goals, key = tuple(row_goal, col_goal),
    # values = list with (row, col) deadlocks

    def __init__(self):
        self.level = []
        self.goals = {}
        self.simple_deadlocks = self.simple_deadlocks()  # sjekk

    def add_goal(self, char, row, col):
        goal = Goal(char, row, col)
        self.level[row][col] = goal
        # Add goal to goal list 1
        if (char in self.goals):
            self.goals[char].append(goal)
        else:
            self.goals[char] = [goal]
        # Add goal to goal list 2
        self.goals_by_pos[(row, col)] = goal

    # static information
    def simple_deadlocks(self, goal_state):
        """
        This type of deadlock is "simple", because it just needs one box to create it.
        simple deadlocks are static - that means the squares creating a simple deadlock are there at level start and during the whole game play.
        Precalculated at the time the level is loaded for playing.
        """
        # make a state
        # delete all boxes and agents from the board
        # place one box at the goal square
        # PULL the box from the goal square to every possible square and put the mark all reached squares as visited
        # every squared not being marked = in list

        # Make the attribute simple_deadlocks which contains all free cells in goal state
        simple_deadlocks = []

        # Remove agents and boxes
        goal_state.agents = {}
        goal_state.boxes = {}
        strategy = StrategyBFS()
        for goal_pos in self.goals_by_pos:
            row, col = goal_pos
            goal_state.boxes[goal_pos] = '1', 'a', 'red', row, col

            simple_deadlocks = remove_visited(row - 1, col, strategy, goal_state, simple_deadlocks)
            simple_deadlocks = remove_visited(row + 1, col, strategy, goal_state, simple_deadlocks)
            simple_deadlocks = remove_visited(row, col - 1, strategy, goal_state, simple_deadlocks)
            simple_deadlocks = remove_visited(row, col + 1, strategy, goal_state, simple_deadlocks)

        return simple_deadlocks


def remove_visited(row, col, strategy, goal_state, simple_deadlocks):
    if goal_state.is_free(row, col):
        goal_state.agents[row, col] = '2', 'red', row - 1, col
        visited_positions = search_deadlocks(strategy, goal_state)

        for pos in visited_positions:
            if pos in simple_deadlocks:
                simple_deadlocks.remove(pos)
        return simple_deadlocks


def search_deadlocks(self, strategy, goal_state):  # BFS search
    strategy.add_to_frontier(goal_state)
    visited = []  # list with tuple of non-deadlocks
    iterations = 0
    while True:
        if strategy.frontier_empty:
            return visited
        leaf = strategy.get_and_remove_leaf()
        strategy.add_to_explored(leaf)
        visited.append(leaf.boxes.keys())  # box_pos or maybe want agent ?

        for agent in leaf.agents.values():
            if agent.id_ == self.id_:
                agent_row = agent.row
                agent_col = agent.col
        children = leaf.get_children_for_agent(self.id_, agent_row, agent_col, PULL_ACTIONS)
        for child_state in children:
            if not strategy.is_explored(child_state) and not strategy.in_frontier(child_state):
                strategy.add_to_frontier(child_state)
        iterations += 1
