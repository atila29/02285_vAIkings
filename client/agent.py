import sys
import random
from action import ActionType, ALL_ACTIONS, UnfoldedAction, Action, Dir
from level import AgentElement
from box import Box
from state import State, LEVEL
from strategy import StrategyBestFirst
from heuristics import Heuristic


class Agent:
    color: str  # maybe enums?
    name: str
    row: int
    col: int

    def __init__(self, id, color, row, col):
        self.row = row
        self.col = col
        self.color = color
        self.id = id

    def get_children(self, current_state):
        children = []

        for action in ALL_ACTIONS:
            # Determine if action is applicable.
            new_agent_row = self.row + action.agent_dir.d_row
            new_agent_col = self.col + action.agent_dir.d_col
            unfolded_action = UnfoldedAction(action, self.id)
            unfolded_action.agent_from = [self.row, self.col]
            unfolded_action.agent_to = [new_agent_row, new_agent_col]

            if action.action_type is ActionType.Move:
                # Check if move action is applicable
                if current_state.is_free(new_agent_row, new_agent_col):
                    # Create child
                    child = State(current_state)
                    # update agent location
                    child.agents.pop((self.row, self.col))
                    child.agents[new_agent_row, new_agent_col] = AgentElement(self.id, self.color, new_agent_row, new_agent_col)
                    #update unfolded action
                    unfolded_action.required_free = unfolded_action.agent_to
                    unfolded_action.will_become_free = unfolded_action.agent_from
                    #Save child
                    child.unfolded_action = unfolded_action
                    children.append(child)
            elif action.action_type is ActionType.Push:
                # Check if push action is applicable
                if (new_agent_row, new_agent_col) in current_state.boxes:
                    if current_state.boxes[(new_agent_row, new_agent_col)].color == self.color:
                        new_box_row = new_agent_row + action.box_dir.d_row
                        new_box_col = new_agent_col + action.box_dir.d_col
                        if current_state.is_free(new_box_row, new_box_col):
                            # Create child
                            child = State(current_state)
                            # update agent location
                            child.agents.pop((self.row, self.col))
                            child.agents[new_agent_row, new_agent_col] = AgentElement(self.id, self.color,
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
                if current_state.is_free(new_agent_row, new_agent_col):
                    box_row = self.row + action.box_dir.d_row
                    box_col = self.col + action.box_dir.d_col
                    if (box_row, box_col) in current_state.boxes:
                        if current_state.boxes[box_row, box_col].color == self.color:
                            # Create Child
                            child = State(current_state)
                            # update agent location
                            child.agents.pop((self.row, self.col))
                            child.agents[new_agent_row, new_agent_col] = AgentElement(self.id, self.color,
                                                                                      new_agent_row, new_agent_col)
                            # update box location
                            box = child.boxes.pop((box_row, box_col))
                            child.boxes[self.row, self.col] = Box(box.name, box.color, self.row, self.col)
                            #update unfolded action
                            unfolded_action.box_from = [box.row, box.col]
                            unfolded_action.box_to = [self.row, self.col]
                            unfolded_action.required_free = unfolded_action.agent_to
                            unfolded_action.will_become_free = unfolded_action.box_from
                            #Save child
                            child.unfolded_action = unfolded_action
                            children.append(child)
            elif action.action_type is ActionType.NoOp:
                child = State(current_state)
                #Save child
                child.unfolded_action = unfolded_action
                children.append(child)
        #Shuffle children ? 
        return children

    def __repr__(self):
        return self.color + " Agent with letter " + self.name

    def __str__(self):
        return self.name

"""
    "Interface" for implementation of BDI Agent
"""
class BDIAgent(Agent):

    def __init__(self,
                 id,
                 color,
                 row,
                 col,
                 initial_beliefs):

        super().__init__(id, color, row, col)
        self.beliefs = initial_beliefs
        self.deliberate()
        self.current_plan = None


    def brf(self, p):  # belief revision function, return new beliefs (updated in while-loop)
        self.beliefs = p
    
    # Updates desires and intentions 
    def deliberate(self):  
        self.desires = self.options()
        self.intentions = self.filter()

    def options(self) -> '?':  # used in deliberate
        return self.desires

    def filter(self) -> '?':  # used in deliberate
        return self.intentions

    def sound(self) -> 'Bool':  # returns true/false, if sound return true
        return True

    def succeeded(self) -> 'Bool':
        return False

    def impossible(self) -> 'Bool':
        return False

    def reconsider(self) -> 'Bool':
        return True

    #default NoOp plan
    def plan(self) -> '[UnfoldedAction, ...]':
        self.current_plan=[UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id)]
        return self.current_plan

    def get_next_action(self,p) -> 'UnfoldedAction':
        self.brf(p)
        if len(self.current_plan) != 0 and not self.succeeded() and not self.impossible(): 
            if self.reconsider():
                self.deliberate()
            if not(self.sound()):
                self.plan()
        self.deliberate()
        self.plan()
        return self.current_plan[0]

    


class BDIAgent1(BDIAgent):

    def __init__(self,
                 id,
                 color,
                 row,
                 col,
                 initial_beliefs):
        super().__init__(id, color, row, col, initial_beliefs)

    def brf(self, p):  # belief revision function, return new beliefs (updated in while-loop)
        # return updated state
        if self.beliefs != p:  # if the world has changed
            self.beliefs = p

    def deliberate(self):  # choose goal - either to a box or to a goal
        #go = [self.row, self.col]   default
        intention = {}
        minimum_so_far = float("inf")
        minimum_box = None
        minimum_goal = None
        for box in self.beliefs.boxes.values():
            for goal in LEVEL.goals_by_pos.values():
                dist_box_goal = abs(goal.row - box.row) + abs(goal.col - box.col) # dist from box to goal
                dist_agt_box = abs(self.row - box.row) + abs(self.col - box.col) # dist from agent to box
                dist = dist_box_goal + dist_agt_box # total dist
                if dist < minimum_so_far:
                    minimum_so_far = dist
                    minimum_box = box
                    minimum_goal = goal
        return [minimum_box, minimum_goal]# [box, goal] with the least distance



    def search_action(self) -> '[Action, ...]':
        heuristic = self.beliefs.Heuristic()
        strategy = StrategyBestFirst(heuristic.f()) 
        print('Starting search with strategy {}.'.format(strategy), file=sys.stderr, flush=True)
        strategy.add_to_frontier(self.beliefs)  # current state
        iterations = 0

        while True:
            if strategy.frontier_empty():
                return None
            leaf = strategy.get_and_remove_leaf()  # state
            if leaf.check_goal_status(): # if the leaf is a goal stat -> extract plan
                return leaf.extract_plan()  # return actions
            strategy.add_to_explored(leaf) # if not goal, contuniue to explore
            for child_state in leaf.get_children(): 
                if not strategy.is_explored(child_state) and not strategy.in_frontier(child_state):
                    strategy.add_to_frontier(child_state)
            iterations += 1

    """
        Used in the search, for extracting a plan when reaching a goal state
    """
    def extract_plan(self) -> '[Actions, ...]':
        # self.brf(current_state)
        # self.deliberate()
        states_in_plan = []
        actions_in_plan = []
        state = self # current state
        while not state.is_initial_state():
            states_in_plan.append(state)
            # action from parent state to current state added to actions
            actions_in_plan.append(state.unfolded_action)
            state = state.parent # one level uo
        actions_in_plan = actions_in_plan.reverse() # actions in executable order
        return actions_in_plan # return actions

    """
        Called by client to get next plan of action
    """
    def get_next_action(self, current_state) -> 'UnfoldedAction':
        children = self.get_children(current_state)
        return random.choice(children).unfolded_action
        #have to check if the intentions are executable
        # self.intentions # [box, goal] : dist
        # self.beliefs # current state
        # list_of_actions = self.search_action()
        # return list_of_actions.pop(0) # return first unfolded action in the plan

"""
    Example BDI agent.
    
    The agent will choose a box and a corresponding goal and try to put that box on that goal 
    until the goal has a box on it with the right letter.
    
    INPUT:
            depth :     Number of steps we look forward
            heuristic:  Function used to evaluate the best step (Depending on the chosen intentions)

    When making a plan the agent will look "depth" steps ahead, where depth is given as an input.
    It will then return the first step of the plan that will result in the state with the best heuristic.
   
    Beliefs:        current_state 
    Desires:        All goals need a box        
    Intentions:     Put box X on goal Y     (Saved as [box, goal])
    Deliberation:   Pick a goal without a box that has a box of your own color somewhere on the map. 
                    Pick one of these boxes to put on the goal.
                    If no such box exists it will just move/push/pull randomnly.
"""
class NaiveBDIAgent(BDIAgent):
    def __init__(self,
                 id,
                 color,
                 row,
                 col,
                 initial_beliefs, 
                 heuristic,
                 depth = 1):
        
        super().__init__(id, color, row, col, initial_beliefs)
        self.n = depth
        self.h = heuristic

    #Choose box and goal and save in intentions as [box, goal]
    #Right now chooses first box in list of right color that has an open goal
    def deliberate(self) :
        box = None
        #find box of the same color
        for b in self.beliefs.boxes.values():
            if b.color == self.color:
                #see if there is a goal that need this box
                for g in LEVEL.goals[b.name]:
                    if not self.beliefs.is_goal_satisfied(g):
                        box = b
                        goal = g
        if box == None:
            self.intentions = None #: When no box to choose default to random
        else:
            self.intentions = (box, goal)
        
        return self.intentions 

    def plan(self):
        if self.intentions is None:
            super().plan()
        else:            
            return self.single_agent_search()

    # Check if the goal still needs a box (Another agent might have solved it)
    def reconsider(self) -> 'Bool':
        return self.succeeded()
        
    # Check if first action is applicable
    def impossible(self) -> 'Bool':
        action = self.current_plan[0]
        #required_free still free?
        if not self.beliefs.is_free(*action.required_free):
            return True
        #if box_from != [] check if a box is still there and right color
        if action.box_from != []:
            if tuple(action.box_from) in self.beliefs.boxes and self.beliefs.boxes[tuple(action.box_from)].color == self.color:
                return False 
            return True
        else:
            return False

    # Check if goal achieved
    def succeeded(self) -> 'Bool':
        if self.intentions is not None:
            return self.beliefs.is_goal_satisfied(self.intentions[1])
        return True

    # TODO: implement
    def single_agent_search(self) -> '[UnfoldedAction, ...]':
        raise NotImplementedError 
    
