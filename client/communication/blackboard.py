from logger import log
from state import LEVEL
from communication.performative import CfpMoveSpecificBoxTo
from communication.contract import Contract
from communication.request import Request
from cave import Cave
from passage import Passage

class Blackboard:
    def __init__(self):
        self.claimed_goals = {}     # key is goal position, value is agentId
        self.claimed_boxes = {}     # key is boxId, value is agentId
        #self.tasks = {}            # key is agentId, value is agent intention
        self.requests = {}          # key is agentId, value is [Request, Request]
        self.claimed_passages = {}  # key is agent_id
        self.claimed_caves = {}     # key is agent_id
    
    def print_status(self, current_state):
        log("The following goals are claimed: {}".format(["Goal {} at location {} by agent {}".format(LEVEL.goals_by_pos[location].letter, location, self.claimed_goals[location]) for location in self.claimed_goals]), "BB", False)
        boxes = []
        for box in current_state.boxes.values():
            if box.id_ in self.claimed_boxes:
                boxes.append("{} by agent {}".format(box, self.claimed_boxes[box.id_]))
        log("The following boxes are claimed: {}".format(boxes), "BB", False)
        log("The following request are on the blackboard: {}".format(self.requests.values()), "BB", False)
        log("The following passages are on the blackboard: {}".format([(p, "Agent {}".format(key)) for key, p in self.claimed_passages.items()]), "BB", False)
        log("The following caves are on the blackboard: {}".format([(p, "Agent {}".format(key)) for key, p in self.claimed_caves.items()]), "BB", False)

    def remove(self, input, agent_id):
        if isinstance(input, Contract):
            self.remove_contract(input, agent_id)
            return
        elif isinstance(input, Request):
            self.remove_request(input, agent_id)
            return
        box, goal = input
        log("Removed {} box with letter {} from the blackboard by agent {}. (ID: {})".format(box.color, box.letter, agent_id, box.id_),"BB", False)
        if box.id_ not in self.claimed_boxes:
            log("box with letter {} and color {} not on bb".format(box.letter, box.color))
        self.claimed_boxes.pop(box.id_)
        
        self.claimed_goals.pop((goal.row, goal.col))


    def remove_contract(self, contract, agent_id):
        performative = contract.performative
        if isinstance(performative, CfpMoveSpecificBoxTo):
            box = performative.box
            log("Removed {} box with letter {} from the blackboard by agent {}. (ID: {})".format(box.color, box.letter, agent_id, box.id_),"BB", False)
            if box.id_ not in self.claimed_boxes:
                log("box with letter {} and color {} not on bb".format(performative.box.letter, performative.box.color))
            self.claimed_boxes.pop(box.id_)
            if performative.location in self.claimed_goals:
                self.claimed_goals.pop(performative.location)

    def add(self, input, agent_id):
        
        if isinstance(input, Contract):
            self.add_contract(input, agent_id)
            return
        elif isinstance(input, Request):
            self.add_request(input, agent_id)
            return
        box, goal = input
        log("Added {} box with letter {} to the blackboard by agent {}. (ID: {})".format(box.color, box.letter, agent_id, box.id_),"BB", False)
        self.claimed_boxes[box.id_] = agent_id
        self.claimed_goals[(goal.row, goal.col)] = agent_id
    
    def add_contract(self, contract, agent_id):
        performative = contract.performative
        if isinstance(performative, CfpMoveSpecificBoxTo):
            box = performative.box
            log("Added {} box with letter {} to the blackboard by agent {}. (ID: {})".format(box.color, box.letter, agent_id, box.id_),"BB", False)
            self.claimed_boxes[box.id_] = agent_id
            if performative.location in LEVEL.goals_by_pos:
                self.claimed_goals[performative.location] = agent_id

    def add_request(self, request, agent_id):
        log("Agent {} added request {} ".format(agent_id, request), "BB_UPDATE", False)
        if agent_id in self.requests:
            self.requests[agent_id].append(request)
        else:
            self.requests[agent_id] = [request]

    def remove_request(self, request, agent_id):
        log("Agent {} removed request {} ".format(agent_id, request), "BB_UPDATE", False)
        self.requests[agent_id].remove(request)
        if len(self.requests[agent_id]) == 0:
            self.requests.pop(agent_id)

    def claim_cave(self, agent_id, cave):
        if agent_id in self.claimed_caves:
            if cave in self.claimed_caves[agent_id]:
                log("Cave {} already claimed by the agent".format(cave.id_), "ERROR?")
        else:
            self.claimed_caves[agent_id] = []

        self.claimed_caves[agent_id].append(cave)

    def remove_claim_cave(self, agent_id, cave):
        self.claimed_caves[agent_id].remove(cave)
        if len(self.claimed_caves[agent_id]) == 0:
            self.claimed_caves.pop(agent_id)

    def claim_passage(self, agent_id, passage):
        if agent_id in self.claimed_passages:
            if passage in self.claimed_passages[agent_id]:
                raise RuntimeError("passage {} already claimed".format(passage.id_))
        else:
            self.claimed_passages[agent_id] = []

        self.claimed_passages[agent_id].append(passage)

    def remove_claim_passage(self, agent_id, passage):
        self.claimed_passages[agent_id].remove(passage)
        if len(self.claimed_passages[agent_id]) == 0:
            self.claimed_passages.pop(agent_id)

    def claim(self, agent_id, input):
        log("Agent {} claimed {}".format(agent_id, input), "CLAIM", False)
        if isinstance(input, Cave):
            self.claim_cave(agent_id, input)
        elif isinstance(input, Passage):
            self.claim_passage(agent_id, input)
        else:
            raise NotImplementedError

    def remove_claim(self, agent_id, input):
        log("Agent {} removed claimed on {}".format(agent_id, input), "CLAIM", False)
        if isinstance(input, Cave):
            self.remove_claim_cave(agent_id, input)
        elif isinstance(input, Passage):
            self.remove_claim_passage(agent_id, input)
        else:
            raise NotImplementedError

    def request_is_there(self, agent_id, request): 
        if agent_id in self.requests:
            for req in self.requests[agent_id]:
                if set(req.area) == set(request.area):
                    return True
        return False
        

BLACKBOARD = Blackboard()


