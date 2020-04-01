from action import ActionType, ALL_ACTIONS, UnfoldedAction
from level import AgentElement
from box import Box
from state import State, LEVEL
from strategy import StrategyBestFirst
from heuristics import Heuristic
import sys
import random   #used for testing


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
                #print('Agent at :' + str((self.row, self.col)) + "figuring out if it can " + str(action), file=sys.stderr, flush=True)
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


class BDIAgent(Agent):

    def __init__(self,
                 id,
                 color,
                 row,
                 col,
                 initial_beliefs,
                 initial_intentions):

        super().__init__(id, color, row, col)
        self.beliefs = initial_beliefs
        self.intentions = self.deliberate()

        # self.path = [] #tar vare på veien agenten beveger seg

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

    # Not needed after adding unfoldedAction to state
    # def get_action(self, current_state): 
    #     # get the only action possible to execute from parent state to current state
    #     parent_state = current_state.parent 
    #     children, children_and_actions = parent_state.get_children() # get list and dict 

    #     for key,value in children_and_actions:
    #         if key == current_state:
    #             return value # returning action from parent to current state

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
    def agent_action_plan(self, current_state):
        children = self.get_children(current_state)
        return random.choice(children).unfolded_action
        #have to check if the intentions are executable
        # self.intentions # [box, goal] : dist
        # self.beliefs # current state
        # list_of_actions = self.search_action()
        # return list_of_actions.pop(0) # return first unfolded action in the plan


# def run_game():
#     agent = BDIAgent()
#     state = State()

#     while True:
#         p = agent.get_next_percept()
#         agent.beliefs = agent.brf(p)
#         agent.intentions = agent.deliberate()
#         plan = state.extract_plan(agent.beliefs, agent.intentions)
#         while not plan == [] and not agent.suceeded() and not agent.impossible():
#             agent.execute(plan.pop([0]))  # execute first step in plan, and removes step from plan
#             p = agent.get_next_percept()
#             agent.beliefs = agent.brf(p)
#             if agent.reconsider():
#                 agent.intentions = agent.deliberate()  # Intention reconsideration
#             if not agent.sound(plan):
#                 plan = state.extract_plan(agent.beliefs, agent.intentions)


# if __name__ == '__main__':
#     run_game()