from action import ActionType, ALL_ACTIONS, Action
from level import AgentElement
from box import Box
from state import State
from strategy import StrategyBestFirst



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

            if action.action_type is ActionType.Move:
                # Check if move action is applicable
                if current_state.is_free(new_agent_row, new_agent_col):
                    # Create child
                    child = State(current_state)
                    # update agent location
                    child.agents.pop((self.row, self.col))
                    child.agents[new_agent_row, new_agent_col] = AgentElement(self.id, self.color, new_agent_row,
                                                                              new_agent_col)
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
                            # Save child
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
                            # save child
                            children.append(child)

        # Shuffle children
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
        for box in self.beliefs.boxes:
            for goal in self.beliefs.goals:
                dist_box_goal = abs(goal.row - box.row) + abs(goal[1] - box[1])
                dist_agt_box = abs(self.row - box.row) + abs(self.col - box.col)
                dist = dist_box_goal + dist_agt_box
                intention[box, goal] = dist
        return min(intention) # [box, goal]



    def search(self) -> '[State, ...]':
        strategy = StrategyBestFirst()
        print('Starting search with strategy {}.'.format(strategy), file=sys.stderr, flush=True)
        strategy.add_to_frontier(self.beliefs)  # current state

        iterations = 0
        while True:
            if strategy.frontier_empty():
                return None

            leaf = strategy.get_and_remove_leaf()  # state

            if leaf.check_goal_status():
                return leaf.extract_plan()  # how is plan represented ?

            strategy.add_to_explored(leaf)
            for child_state in leaf.get_children():  # The list of expanded states is shuffled randomly; see state.py.
                if not strategy.is_explored(child_state) and not strategy.in_frontier(child_state):
                    strategy.add_to_frontier(child_state)

            iterations += 1

    def extract_plan(self) -> '[State, ...]':
        plan = []
        state = self
        while not state.is_initial_state():
            plan.append(state)
            state = state.parent
        plan.reverse()
        return plan



    def agent_search_plan(self):  #li
        #have to check if the intentions are executable
        self.intentions # [box, goal] : dist
        self.beliefs # current state


        #søk
        #strategi - Best first strategy
        #heuristikk


        return plan

    # search


    def extract_plan(self, current_state) -> '[Action,...]':  # include this function?
        self.brf(current_state)
        #self.deliberate()
        plan = self.plan()
        return plan  # only return the first step
        #return unfolded_action ??


"""
    E.g. Version 2 from slide 24 week 5
        1. & 2. removed since loop is in client instead
        3. get next percept ρ, in our case the current state;
        4. Update beliefs, B := brf (B,ρ);
        5. Update Intentions, I := deliberate(B);
        6. Make plan, π:= plan(B,I);
        7. Return plan π
Q: Do we need to save in new variables 
until we know from server that the plan is OK?
Q: In case of conflict we might need to make some agents replan,
How do we get them to choose another plan?
    Idea 1: Give them a number i, 0 as default, to tell them to choose the
    'ith best' plan.
"""

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
