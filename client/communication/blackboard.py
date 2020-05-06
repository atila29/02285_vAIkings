from util import log
from state import LEVEL
from communication.performative import CfpMoveSpecificBoxTo
from communication.contract import Contract

class Blackboard:
    def __init__(self):
        self.claimed_goals = {} # key is goal position, value is agentId
        self.claimed_boxes = {} # key is boxId, value is agentId
        #self.tasks = {}         # key is agentId, value is agent intention
    
    def print_status(self, current_state):
        log("The following goals are claimed: {}".format([LEVEL.goals_by_pos[location] for location in self.claimed_goals]), "BB", False)
        boxes = []
        for box in current_state.boxes.values():
            if box.id_ in self.claimed_boxes:
                boxes.append(box)
        log("The following boxes are claimed: {}".format(boxes), "BB", False)

    def remove(self, input):
        if isinstance(input, Contract):
            self.remove_contract(input)
            return
        box, goal = input
        self.claimed_boxes.pop(box.id_)
        self.claimed_goals.pop((goal.row, goal.col))


    def remove_contract(self, contract):
        performative = contract.performative
        if isinstance(performative, CfpMoveSpecificBoxTo):
            self.claimed_boxes.pop(performative.box.id_)
            if performative.location in self.claimed_goals:
                self.claimed_goals.pop(performative.location)

    def add(self, input, agent_id):
        if isinstance(input, Contract):
            self.add_contract(input, agent_id)
            return
        box, goal = input
        self.claimed_boxes[box.id_] = agent_id
        self.claimed_goals[(goal.row, goal.col)] = agent_id
    
    def add_contract(self, contract, agent_id):
        performative = contract.performative
        if isinstance(performative, CfpMoveSpecificBoxTo):
            self.claimed_boxes[performative.box.id_] = agent_id
            if performative.location in LEVEL.goals_by_pos:
                self.claimed_goals[performative.location] = agent_id
        

BLACKBOARD = Blackboard()


