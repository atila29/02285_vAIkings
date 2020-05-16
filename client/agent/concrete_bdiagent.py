from agent.bdiagent import BDIAgent
from communication.request import Request
from communication.contract import Contract
from action import ActionType

class ConcreteBDIAgent(BDIAgent):
    
    def add_subgoal(self, goal):
        self.desires['goals'].append(goal)

    def deliberate(self):  
        raise NotImplementedError 

    def sound(self) -> 'Bool':  # returns true/false, if sound return true
        raise NotImplementedError 

    #copied from CNETAgent
    def succeeded(self) -> 'Bool':
        if self.intentions is None:
            return True
        if isinstance(self.intentions, Request):
            return len(self.current_plan) == 0
        if isinstance(self.intentions, Contract):
            box = self.intentions.performative.box
            location = self.intentions.performative.location 
            if location in self.beliefs.boxes and self.beliefs.boxes[location].id_ == box.id_:
                return True
            return False
        return self.beliefs.is_goal_satisfied(self.intentions[1])  
    
    #TODO: When we call impossible we probably mean is_next_action_impossible()
    def impossible(self) -> 'Bool':
        return False

    def reconsider(self) -> 'Bool':
        return self.succeeded()

    #default NoOp plan
    def plan(self) -> '[UnfoldedAction, ...]':
        raise NotImplementedError
    
    #old impossible from CNETAgent
    def is_next_action_impossible(self):
        action = self.current_plan[0] #Unfoldedaction
        if action.action.action_type == ActionType.NoOp:
            return False
        #required_free still free?
        if not(self.beliefs.is_free(*action.required_free)):
            return True
        if action.box_from is not None:
            if not(action.box_from in self.beliefs.boxes and self.beliefs.boxes[action.box_from].color == self.color):
                return True 
        return False
