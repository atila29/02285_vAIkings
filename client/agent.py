import sys
import random
from action import ActionType, ALL_ACTIONS, UnfoldedAction, Action, Dir
from level import AgentElement, Box
from state import State, LEVEL
from strategy import StrategyBestFirst
from heuristics import Heuristic
from util import log


class Agent:
    color: str  # maybe enums?
    id_: str
    row: int
    col: int

    def __init__(self, id_, color, row, col):
        self.row = row
        self.col = col
        self.color = color
        self.id_ = id_

    def get_children(self, current_state):
        children = []

        for action in ALL_ACTIONS:
            # Determine if action is applicable.
            new_agent_row = self.row + action.agent_dir.d_row
            new_agent_col = self.col + action.agent_dir.d_col
            unfolded_action = UnfoldedAction(action, self.id_)
            unfolded_action.agent_from = (self.row, self.col)
            unfolded_action.agent_to = (new_agent_row, new_agent_col)

            if action.action_type is ActionType.Move:
                # Check if move action is applicable
                if current_state.is_free(new_agent_row, new_agent_col):
                    # Create child
                    child = State(current_state)
                    # update agent location
                    child.agents.pop((self.row, self.col))
                    child.agents[new_agent_row, new_agent_col] = AgentElement(self.id_, self.color, new_agent_row, new_agent_col)
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
                            child.agents[new_agent_row, new_agent_col] = AgentElement(self.id_, self.color,
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
                if current_state.is_free(new_agent_row, new_agent_col):
                    box_row = self.row + action.box_dir.d_row
                    box_col = self.col + action.box_dir.d_col
                    if (box_row, box_col) in current_state.boxes:
                        if current_state.boxes[box_row, box_col].color == self.color:
                            # Create Child
                            child = State(current_state)
                            # update agent location
                            child.agents.pop((self.row, self.col))
                            child.agents[new_agent_row, new_agent_col] = AgentElement(self.id_, self.color,
                                                                                      new_agent_row, new_agent_col)
                            # update box location
                            box = child.boxes.pop((box_row, box_col))
                            child.boxes[self.row, self.col] = Box(box.id_, box.letter, box.color, self.row, self.col)
                            #update unfolded action
                            unfolded_action.box_from = (box.row, box.col)
                            unfolded_action.box_to = (self.row, self.col)
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
        return self.color + " Agent with letter " + self.id_

    def __str__(self):
        return self.id_

"""
    "Interface" for implementation of BDI Agent
"""
class BDIAgent(Agent):

    def __init__(self,
                 id_,
                 color,
                 row,
                 col,
                 initial_beliefs):

        super().__init__(id_, color, row, col)
        self.beliefs = initial_beliefs
        self.deliberate()
        self.current_plan = []


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
        self.current_plan=[UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_)]
        return self.current_plan

    def get_next_action(self, p) -> 'UnfoldedAction': #p is the perception
        self.brf(p)
        if len(self.current_plan) != 0 and (not self.succeeded()) and (not self.impossible()): 
            if self.reconsider():
                self.deliberate()
            if not(self.sound()):
                self.plan()
        else:
            # log("Agent " + str(self.id_) +" at position " + str((self.row, self.col)) + " is replanning because:")
            # if len(self.current_plan) == 0:
            #     log("Length of current plan, was 0")
            # elif self.succeeded():
            #     log("Previous plan succeeded")
            # elif self.impossible:
            #     log("Current plan: " + str(self.current_plan)+ " was impossible")
            self.deliberate()
            self.plan()
        return self.current_plan[0] #what if empty?
        

    


class BDIAgent1(BDIAgent):

    def __init__(self,
                 id_,
                 color,
                 row,
                 col,
                 initial_beliefs):
        super().__init__(id_, color, row, col, initial_beliefs)

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
        strategy = StrategyBestFirst(heuristic, self) 
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
                 id_,
                 color,
                 row,
                 col,
                 initial_beliefs, 
                 #heuristic,
                 depth = 1):
        
        super().__init__(id_, color, row, col, initial_beliefs)
        self.n = depth
        #self.h = heuristic
        self.heuristic = Heuristic(self)

    #Choose box and goal and save in intentions as [box, goal]
    #Right now chooses first box in list of right color that has an open goal
    def deliberate(self) :
        box = None
        #find box of the same color
        for b in self.beliefs.boxes.values():
            if b.color == self.color:
                if b.letter in LEVEL.goals:
                    #see if there is a goal that need this box
                    for g in LEVEL.goals[b.letter]:
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
        if action.required_free is not None and not self.beliefs.is_free(*action.required_free):
            return True
        #if box_from != [] check if a box is still there and right color
        if action.box_from != []:
            if action.box_from in self.beliefs.boxes and self.beliefs.boxes[action.box_from].color == self.color:
                return False 
            return True
        else:
            return False

    # Check if goal achieved
    def succeeded(self) -> 'Bool':
        if self.intentions is not None:
            return self.beliefs.is_goal_satisfied(self.intentions[1])
        return True

    def single_agent_search(self) -> '[UnfoldedAction, ...]':
        strategy = StrategyBestFirst(self.heuristic, self)
        #print('Starting search with strategy {}.'.format(strategy), file=sys.stderr, flush=True)
        #ta inn level her ?
        strategy.add_to_frontier(self.beliefs)  # current state
        
        states_in_depth_n =[]
        self.current_plan =[]
        initial_g = self.beliefs.g
        iterations = 0
        next_state = (self.beliefs, self.heuristic.f(self.beliefs))
        while True:
            #log("Iteration: " + str(iterations))
            #log("Length of frontier" + str(len(strategy.frontier)))
            iterations = iterations + 1
            #Pick a leaf to explore
            if strategy.frontier_empty():
            # if strategy.frontier_empty() or iterations > 1000:
                #log("frontier is empty")
                break
            leaf = strategy.get_and_remove_leaf()  # 
            
            #If we found solution 
            if leaf.is_goal_satisfied(self.intentions[1]):  # if the leaf is a goal stat -> extract plan
                #log("found solution", "info")
                state = leaf  # current state
                while not state.is_current_state(self.beliefs):
                    self.current_plan.append(state.unfolded_action)
                    state = state.parent  # one level up
                return self.current_plan.reverse()
           
            #If the state is not too deep, generate children and add to frontier
            if (leaf.g - initial_g) < self.n:
                        #Find agent position in this state
                for agent in leaf.agents.values(): 
                    if agent.id_ == self.id_:
                        agent_row = agent.row
                        agent_col = agent.col
                children = leaf.get_children_for_agent(self.id_, agent_row, agent_col)
                for child_state in children:
                    if not strategy.is_explored(child_state) and not strategy.in_frontier(child_state):
                        strategy.add_to_frontier(child_state)
                        h = self.heuristic.f(child_state)
                        if h < next_state[1]:
                            next_state = (child_state, h)  
            
            strategy.add_to_explored(leaf)  

        #If no solution found, pick best state in depth n
        #log("didn't find solution")\
        #run through list pick the one with best heuristic
        # state = min(states_in_depth_n, key = lambda state: self.heuristic.f(state))
        state = next_state[0]
        
        #log("Best state in depth n" + str(state))

        if state.is_current_state(self.beliefs):
            self.current_plan = [UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_)]

        #extract plan
        while not state.is_current_state(self.beliefs):
            self.current_plan.append(state.unfolded_action)
            state = state.parent  # one level up
        #log("Extracted plan (in reverse)" + str(self.current_plan))
        log("Searching done for agent " + str(self.id_) + ", took best state with plan (reversed)" + str(self.current_plan))
        return self.current_plan.reverse()

            
        
class NaiveIterativeBDIAgent(BDIAgent):
    def __init__(self,
                 id_,
                 color,
                 row,
                 col,
                 initial_beliefs, 
                 #heuristic,
                 depth = 1):
        
        super().__init__(id_, color, row, col, initial_beliefs)
        self.n = depth
        #self.h = heuristic
        self.heuristic = Heuristic(self)

    #Choose box and goal and save in intentions as [box, goal]
    #Right now chooses first box in list of right color that has an open goal
    def deliberate(self) :
        box = None
        #find box of the same color
        for b in self.beliefs.boxes.values():
            if b.color == self.color:
                if b.letter in LEVEL.goals:
                    #see if there is a goal that need this box
                    for g in LEVEL.goals[b.letter]:
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
        #log("status", str(self.id_))
        #self.beliefs.print_current_state()
        if action.action.action_type == ActionType.NoOp:
            #log("Agent " + str(self.id_) + " can safely NoOp")
            return False
        #required_free still free?
        if not(self.beliefs.is_free(*action.required_free)):
            #log("space no longer free: "+ str(action.required_free))
            return True
        # else:
        #     log("Space " + str(action.required_free) + " is free")
        #Moving box?
        if action.box_from is not None:
            if not(action.box_from in self.beliefs.boxes and self.beliefs.boxes[action.box_from].color == self.color):
                #log("failed to find box of color" + str(self.color) +" in wanted location" + str(action.box_from))
                return True 
        #log("Agent " + str(self.id_) +" at position " + str((self.row, self.col)) + " thinks it is safe to " + str(action.action))
        return False

        # if (action.required_free is not None) and (not self.beliefs.is_free(action.required_free[0], action.required_free[1])):
        #     log("Space no longer free: " + str(action.required_free))
        #     return True
        # #if box_from != [] check if a box is still there and right color
        # if action.box_from is not None:
        #     if action.box_from in self.beliefs.boxes and self.beliefs.boxes[action.box_from].color == self.color:
        #         return False 
        #     return True
        # else:
        #     return False

    # Check if goal achieved
    def succeeded(self) -> 'Bool':
        if self.intentions is not None:
            return self.beliefs.is_goal_satisfied(self.intentions[1])
        return True

    def single_agent_search(self) -> '[UnfoldedAction, ...]':
        strategy = StrategyBestFirst(self.heuristic, self)
        #print('Starting search with strategy {}.'.format(strategy), file=sys.stderr, flush=True)
        #ta inn level her ?
        strategy.add_to_frontier(self.beliefs)  # current state
        
        states_in_depth_n =[]
        self.current_plan =[]
        initial_g = self.beliefs.g
        iterations = 0
        next_state = (self.beliefs, self.heuristic.f(self.beliefs))
        while True:
            #log("Iteration: " + str(iterations))
            #log("Length of frontier" + str(len(strategy.frontier)))
            iterations = iterations + 1
            #Pick a leaf to explore
            if strategy.frontier_empty() or iterations > 1000:
                #log("frontier is empty")
                break
            leaf = strategy.get_and_remove_leaf()  # 
            
            #If we found solution 
            if leaf.is_goal_satisfied(self.intentions[1]):  # if the leaf is a goal stat -> extract plan
                #log("found solution", "info")
                state = leaf  # current state
                while not state.is_current_state(self.beliefs):
                    self.current_plan.append(state.unfolded_action)
                    state = state.parent  # one level up
                return self.current_plan.reverse()
           
            #Find agent position in this state
            for agent in leaf.agents.values(): 
                if agent.id_ == self.id_:
                    agent_row = agent.row
                    agent_col = agent.col
            children = leaf.get_children_for_agent(self.id_, agent_row, agent_col)
            for child_state in children:
                if not strategy.is_explored(child_state) and not strategy.in_frontier(child_state):
                    strategy.add_to_frontier(child_state)
                    h = self.heuristic.f(child_state)
                    if h < next_state[1]:
                        next_state = (child_state, h)  
            
            strategy.add_to_explored(leaf)  

        #If no solution found, pick best state in depth n
        #log("didn't find solution")\
        #run through list pick the one with best heuristic
        # state = min(states_in_depth_n, key = lambda state: self.heuristic.f(state))
        state = next_state[0]
        
        #log("Best state in depth n" + str(state))

        if state.is_current_state(self.beliefs):
            self.current_plan = [UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_)]

        #extract plan
        while not state.is_current_state(self.beliefs):
            self.current_plan.append(state.unfolded_action)
            state = state.parent  # one level up
        #log("Extracted plan (in reverse)" + str(self.current_plan))
        #log("Searching done for agent " + str(self.id_) + ", took best state with plan (reversed)" + str(self.current_plan))
        return self.current_plan.reverse()


