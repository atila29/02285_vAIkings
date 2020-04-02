import sys
from typing import List, Tuple, Dict
from enum import Enum
from box import Box
from level import LevelElement, Level, Wall, AgentElement
from action import Action, ALL_ACTIONS, Dir, ActionType, UnfoldedAction
import copy

LEVEL = Level()

"""
    Custom object that keeps track of the non-static information about the level
    i.e. the position of boxes and agents
"""
class State(object):
    agents = Dict[Tuple[int, int], AgentElement]
    boxes = Dict[Tuple[int, int], Box]
    g: int
    parent: 'State'
    unfolded_action: 'UnfoldedAction'

    def __init__(self, copy_state: 'State' = None):

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

    def get_children_for_agent(self, agent_id, agent_row, agent_col):
        children = []
        agent = self.agents[agent_row, agent_col]
        if agent.name != agent_id:
            raise RuntimeError("Mismatch between agent ID and position. ID given:" + str(agent_id) + " and position " + str((agent_row, agent_col)) + ". But found " + str(agent.name))
        for action in ALL_ACTIONS:
            # Determine if action is applicable.
            new_agent_row = agent.row + action.agent_dir.d_row
            new_agent_col = agent.col + action.agent_dir.d_col
            unfolded_action = UnfoldedAction(action, agent.id)
            unfolded_action.agent_from = [agent.row, agent.col]
            unfolded_action.agent_to = [new_agent_row, new_agent_col]

            if action.action_type is ActionType.Move:
                # Check if move action is applicable
                if self.is_free(new_agent_row, new_agent_col):
                    # Create child
                    child = State(self)
                    # update agent location
                    child.agents.pop((agent.row, agent.col))
                    child.agents[new_agent_row, new_agent_col] = AgentElement(agent.id, agent.color, new_agent_row, new_agent_col)
                    #update unfolded action
                    unfolded_action.required_free = unfolded_action.agent_to
                    unfolded_action.will_become_free = unfolded_action.agent_from
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
                            child.agents[new_agent_row, new_agent_col] = AgentElement(agent.id, agent.color,
                                                                                        new_agent_row, new_agent_col)
                            # update box location
                            box = child.boxes.pop((new_agent_row, new_agent_col))
                            child.boxes[new_box_row, new_box_col] = Box(box.name, box.color, new_box_row, new_box_col)
                            #update unfolded action
                            unfolded_action.box_from = [box.row, box.col]
                            unfolded_action.box_to = [new_box_row, new_box_col]
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
                            child.agents[new_agent_row, new_agent_col] = AgentElement(agent.id, agent.color,
                                                                                        new_agent_row, new_agent_col)
                            # update box location
                            box = child.boxes.pop((box_row, box_col))
                            child.boxes[agent.row, agent.col] = Box(box.name, box.color, agent.row, agent.col)
                            #update unfolded action
                            unfolded_action.box_from = [box.row, box.col]
                            unfolded_action.box_to = [agent.row, agent.col]
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
        return (goal.row, goal.col) in self.boxes and self.boxes[goal.row, goal.col].name == goal.name

