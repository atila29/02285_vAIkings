from action import ActionType, ALL_ACTIONS
from state import State
from level import AgentElement
from box import Box

class Agent:

    def __init__(self, row, col, color, id):
        self.row = row
        self.col = col
        self.color = color
        self.id = id

    def __str__(self):
        return "Logical agent with ID " + id

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