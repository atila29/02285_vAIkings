# Copied from WarmupAssignment

import heapq
import itertools
import sys
from collections import deque


class StrategyBestFirst():
    counter = itertools.count()  # variable to solve the problem with having multiple elements with the same priority

    # when this happens, heapq.heappop will remove and return the element with the smallest counter
    # starting by default with the number 0

    def __init__(self, heuristic: 'Heuristic', agent: 'BDIAgent'):
        super().__init__()
        self.heuristic = heuristic
        self.frontier = []
        self.frontier_set = set()
        self.explored = set()
        self.agent = agent

    def add_to_explored(self, state: 'State'):
        self.explored.add(state)

    def is_explored(self, state: 'State') -> 'bool':
        return state in self.explored

    def get_and_remove_leaf(self) -> 'State':
        priority, count, leaf = heapq.heappop(self.frontier)  # removes and return the smallest element
        return leaf

    def add_to_frontier(self, state: 'State'):
        priority = self.heuristic  # gets the priority from the heuristic function f
        count = next(StrategyBestFirst.counter)  # advancing the value
        entry = [priority, count, state]  # the values the heap is prioritized by
        heapq.heappush(self.frontier, entry)
        self.frontier_set.add(state)

    def in_frontier(self, state: 'State') -> 'bool':
        return state in self.frontier_set

    def frontier_count(self) -> 'int':
        return len(self.frontier)

    def frontier_empty(self) -> 'bool':
        return len(self.frontier) == 0

    def __repr__(self):
        return 'Best-first Search using {}'.format(self.heuristic)


class StrategyBFS:
    def __init__(self):
        super().__init__()
        self.frontier = deque()
        self.frontier_set = set()
        self.explored = set()

    def add_to_explored(self, state: 'State'):
        self.explored.add(state)

    def is_explored(self, state: 'State') -> 'bool':
        return state in self.explored

    def get_and_remove_leaf(self) -> 'State':
        leaf = self.frontier.popleft()
        self.frontier_set.remove(leaf)
        return leaf

    def add_to_frontier(self, state: 'State'):
        #only adds pull Actions
        self.frontier.append(state)
        self.frontier_set.add(state)

    def in_frontier(self, state: 'State') -> 'bool':
        return state in self.frontier_set

    def frontier_count(self) -> 'int':
        return len(self.frontier)

    def frontier_empty(self) -> 'bool':
        return len(self.frontier) == 0

    def __repr__(self):
        return 'Breadth-first Search'