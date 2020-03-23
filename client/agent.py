from action import ActionType, ALL_ACTIONS
from level import AgentElement
from box import Box
from state import State

class Agent:
    color: str  # maybe enums?
    name: str
    row = -1
    col = -1

    def __init__(self, row, col, color, id):
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
                #Check if move action is applicable
                if current_state.is_free(new_agent_row, new_agent_col):
                    #Create child
                    child = State(current_state)
                    #update agent location
                    child.agents.pop((self.row, self.col))
                    child.agents[new_agent_row, new_agent_col] = AgentElement(self.id, self.color, new_agent_row, new_agent_col)
                    children.append(child)
            elif action.action_type is ActionType.Push:
                #Check if push action is applicable
                if (new_agent_row, new_agent_col) in current_state.boxes:
                    if current_state.boxes[(new_agent_row, new_agent_col)].color == self.color:
                        new_box_row = new_agent_row + action.box_dir.d_row
                        new_box_col = new_agent_col + action.box_dir.d_col
                        if current_state.is_free(new_box_row, new_box_col):
                            #Create child
                            child = State(current_state)
                            #update agent location
                            child.agents.pop((self.row, self.col))
                            child.agents[new_agent_row, new_agent_col] = AgentElement(self.id, self.color, new_agent_row, new_agent_col)
                            #update box location
                            box = child.boxes.pop((new_agent_row, new_agent_col))
                            child.boxes[new_box_row, new_box_col] = Box(box.name, box.color, new_box_row, new_box_col)
                            #Save child
                            children.append(child)
            elif action.action_type is ActionType.Pull:
                #Check if pull action is applicable
                if current_state.is_free(new_agent_row, new_agent_col):
                    box_row = self.row + action.box_dir.d_row
                    box_col = self.col + action.box_dir.d_col
                    if (box_row, box_col) in current_state.boxes:
                        if current_state.boxes[box_row, box_col].color == self.color:
                            #Create Child
                            child = State(current_state)
                            #update agent location
                            child.agents.pop((self.row, self.col))
                            child.agents[new_agent_row, new_agent_col] = AgentElement(self.id, self.color, new_agent_row, new_agent_col)
                            #update box location
                            box = child.boxes.pop((box_row, box_col))
                            child.boxes[self.row, self.col] = Box(box.name, box.color, self.row, self.col)
                            #save child
                            children.append(child)

        #Shuffle children
        return children

    def __repr__(self):
        return self.color + " Agent with letter " + self.name

    def __str__(self):
        return self.name


class BDIAgent(Agent):

    def __init__(self, initial_beliefs, initial_intentions, initial_state):
        self.beliefs = initial_beliefs
        self.intentions = initial_intentions
        # self.path = [] #tar vare på veien agenten beveger seg

    def get_next_percept(self):
        return

    def brf(self, p):  # belief revision function, return new beliefs (updated in while-loop)
        return

    def deliberate(self):  # returns intentions (computed in filter())
        return filter()

    def options(self):  # used in deliberate
        return

    def filter(self):  # used in deliberate
        return

    def sound(self, plan):  # returns true/false, if sound return true
        return

    def suceeded(self):
        return

    def impossible(self):
        return

    def reconsider(self):
        return

    def execute(self, a): #execute an action
        return



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
