import sys
from typing import List, Tuple, Dict
from enum import Enum
from level import LevelElement, Level, Wall, AgentElement, Box, AgentGoal
from action import Action, ALL_ACTIONS, Dir, ActionType, UnfoldedAction
import copy
import random
from logger import log

LEVEL = Level()

"""
    Custom object that keeps track of the non-static information about the level
    i.e. the position of boxes and agents
"""
class State(object):
    agents = Dict[Tuple[int, int], AgentElement]
    boxes = Dict[Tuple[int, int], Box]
    g: int #measure of the depth/time
    parent: 'State'
    unfolded_action: 'UnfoldedAction'

    def __init__(self, copy_state: 'State' = None):

        self._hash = None
        if copy_state is None:
            self.agents = {}
            self.boxes = {}
            self.g = 0
            self.parent = None
            self.unfolded_action = None
        else:
            self.agents = copy.deepcopy(copy_state.agents)
            self.boxes = copy.deepcopy(copy_state.boxes)
            self.g = copy_state.g + 1
            self.parent = copy_state
            self.unfolded_action = copy_state.unfolded_action

        

    def __repr__(self):
        return str((self.agents, self.boxes))

    def __str__(self):
        return self.__repr__()

    def print_current_state(self):
        level_copy = copy.deepcopy(LEVEL.level)
        for pos in self.agents:
            level_copy[pos[0]][pos[1]] = self.agents[pos]
        for pos in self.boxes:
            level_copy[pos[0]][pos[1]] = self.boxes[pos]

        lines =[]
        for row in level_copy:
            line  =[]
            for elm in row:
                line.append(str(elm))
            lines.append(''.join(line))
        print("\n".join(lines), file=sys.stderr, flush=True)

    def is_free(self, row , col) -> 'bool':
        #print('index: ' + str((row, col)), file=sys.stderr, flush=True)
        if (row, col) in self.agents or (row, col) in self.boxes or isinstance(LEVEL.level[row][col], Wall):
            return False
        return True
        
    def is_initial_state(self) -> 'bool':
        return self.parent is None

    def __hash__(self):
        if self._hash is None:
            prime = 31
            _hash = 1
            _hash = _hash * prime + hash(tuple([(agent.row, agent.col) for agent in self.agents.values()]))
            _hash = _hash * prime + hash(tuple([(box.row, box.col) for box in self.boxes.values()]))
            self._hash = _hash
        return self._hash

    def is_current_state(self, state) -> 'bool':
        return self == state

    def get_children_for_agent(self, agent_id, agent_row, agent_col, set_of_actions=ALL_ACTIONS):
        children = []
        #check there is actually an agent
        if (agent_row, agent_col) not in self.agents or self.agents[agent_row, agent_col].id_ != agent_id:
            raise RuntimeError("Mismatch between agent ID and position")
        agent = self.agents[agent_row, agent_col]
        #random.shuffle(set_of_actions) 
        for action in set_of_actions:

            # Determine if action is applicable.
            new_agent_row = agent.row + action.agent_dir.d_row
            new_agent_col = agent.col + action.agent_dir.d_col
            unfolded_action = UnfoldedAction(action, agent.id_)
            unfolded_action.agent_from = (agent.row, agent.col)
            unfolded_action.agent_to = (new_agent_row, new_agent_col)

            if action.action_type is ActionType.Move:
                # Check if move action is applicable
                if self.is_free(new_agent_row, new_agent_col):
                    # Create child
                    child = State(self)
                    # update agent location
                    child.agents.pop((agent.row, agent.col))
                    child.agents[new_agent_row, new_agent_col] = AgentElement(agent.id_, agent.color, new_agent_row, new_agent_col)
                    #update unfolded action
                    unfolded_action.required_free = (new_agent_row, new_agent_col)
                    unfolded_action.will_become_free = (agent.row, agent.col)
                    #Save child
                    child.unfolded_action = unfolded_action
                    children.append(child)
            elif action.action_type is ActionType.Push:
                # Check if push action is applicable
                if (new_agent_row, new_agent_col) in self.boxes:
                    if self.boxes[(new_agent_row, new_agent_col)].color == agent.color:
                        new_box_row = new_agent_row + action.box_dir.d_row
                        new_box_col = new_agent_col + action.box_dir.d_col
                        if self.is_free(new_box_row, new_box_col):
                            # Create child
                            child = State(self)
                            # update agent location
                            child.agents.pop((agent.row, agent.col))
                            child.agents[new_agent_row, new_agent_col] = AgentElement(agent.id_, agent.color,
                                                                                        new_agent_row, new_agent_col)
                            # update box location
                            box = child.boxes.pop((new_agent_row, new_agent_col))
                            child.boxes[new_box_row, new_box_col] = Box(box.id_, box.letter, box.color, new_box_row, new_box_col)
                            #update unfolded action
                            unfolded_action.box_from = (box.row, box.col)
                            unfolded_action.box_to = (new_box_row, new_box_col)
                            unfolded_action.required_free = unfolded_action.box_to
                            unfolded_action.will_become_free = unfolded_action.agent_from
                            #Save child
                            child.unfolded_action = unfolded_action
                            children.append(child)                            
            elif action.action_type is ActionType.Pull:
                # Check if pull action is applicable
                if self.is_free(new_agent_row, new_agent_col):
                    box_row = agent.row + action.box_dir.d_row
                    box_col = agent.col + action.box_dir.d_col
                    if (box_row, box_col) in self.boxes:
                        if self.boxes[box_row, box_col].color == agent.color:
                            # Create Child
                            child = State(self)
                            # update agent location
                            child.agents.pop((agent.row, agent.col))
                            child.agents[new_agent_row, new_agent_col] = AgentElement(agent.id_, agent.color,
                                                                                        new_agent_row, new_agent_col)
                            # update box location
                            box = child.boxes.pop((box_row, box_col))
                            child.boxes[agent.row, agent.col] = Box(box.id_, box.letter, box.color, agent.row, agent.col)
                            #update unfolded action
                            unfolded_action.box_from = (box.row, box.col)
                            unfolded_action.box_to = (agent.row, agent.col)
                            unfolded_action.required_free = unfolded_action.agent_to
                            unfolded_action.will_become_free = unfolded_action.box_from
                            #Save child
                            child.unfolded_action = unfolded_action
                            children.append(child)
            elif action.action_type is ActionType.NoOp:
                child = State(self)
                #Save child
                child.unfolded_action = unfolded_action
                children.append(child)
        #Shuffle children ? 
        return children











    def is_goal_satisfied(self, goal):
        if isinstance(goal, AgentGoal):
            return (goal.row, goal.col) in self.agents and self.agents[goal.row, goal.col].id_ == goal.id_
        return (goal.row, goal.col) in self.boxes and self.boxes[goal.row, goal.col].letter == goal.letter

    def is_box_at_location(self, location, boxid):
        return  location in self.boxes and self.boxes[location].id_ == boxid

    def __eq__(self,other):
        #check agent locations
        for key in self.agents:
            if key not in other.agents or other.agents[key] != self.agents[key]:
                #log("States were NOT equal:" + str(self) +", " + str(other),"Compared states")
                return False
        #check box locations
        for key in self.boxes:
            if key not in other.boxes or other.boxes[key] != self.boxes[key]:
                #log("States were NOT equal:" + str(self) +", " + str(other),"Compared states")
                return False
        #log("States were equal:" + str(self) +", " + str(other),"Compared states")
        return True