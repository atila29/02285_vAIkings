from agent.cnetagent import CNETAgent

from communication.blackboard import BLACKBOARD
from communication.request import Request
from communication.performative import CfpMoveSpecificBoxTo
from communication.contract import Contract

from heuristics import  Heuristic2
from logger import log
from state import LEVEL

import heapq 


class ConcreteCNETAgent(CNETAgent):
    
    #Copied from CNETAgent
    def calculate_proposal(self, performative, cost):
        #search for solution to the problem
        if len(self.desires['contracts']) != 0:
            log("Agent {} refused because it is occupied with another contract".format(self.id_), "BIDDING", False)
            return None
        if isinstance(self.intentions, Request):
            log("Agent {} refused because it is trying to fulfill a request".format(self.id_), "BIDDING", False)
            return None
        #update current_proposal + return cost or None as refusal
        if isinstance(performative, CfpMoveSpecificBoxTo) and performative.box.color == self.color:            
            if isinstance(self.heuristic, Heuristic2):
                cost = self.heuristic.f(self.beliefs, (performative.box,performative.location), self)
            else:
                cost = self.heuristic.f(self.beliefs, (performative.box,performative.location))
        else:
            return None
        if cost == float("inf"):
            log("Agent {} refused because it is unreachable".format(self.id_), "BIDDING", False)
            return None
        self.current_proposal = {}
        self.current_proposal['performative'] = performative
        self.current_proposal['cost'] = cost
        log("Agent {}: I can do it in {} moves".format(self.id_, cost), "BIDDING", False)
        return cost

    #copied from CNETAgent2
    def remove_intentions_from_blackboard(self):
        if self.succeeded():
            log("Agent {} succeeded it's task of {}.".format(self.id_, self.intentions), "BDI", False)
        #Remove contract from desire and BB
        if isinstance(self.intentions, Contract):
            BLACKBOARD.remove(self.intentions, self.id_)
            self.desires['contracts'].pop(0)
        #Remove claim on box and goal on BB, if intention is (box,goal)
        elif isinstance(self.intentions, Request):
            self.completed_request(self.intentions)
        elif self.intentions is not None:
            box, goal = self.intentions
            BLACKBOARD.remove((box,goal), self.id_)
        #Reset intentions
        self.intentions = None

    def add_intentions_to_blackboard(self):
        #Add contract from desire and BB
        if isinstance(self.intentions, Contract):
            BLACKBOARD.add(self.intentions, self.id_)
        #add claim on box and goal on BB, if intention is (box,goal)
        elif isinstance(self.intentions, Request):
            self.commit_to_request(self.intentions)
        elif self.intentions is not None:
            box, goal = self.intentions
            BLACKBOARD.add((box,goal), self.id_)

    def completed_request(self, request):
        log("Agent {} completed its task in helping with a request".format(self.id_), "BDI", False)
        self.intentions = None

        # Remark: Assume only one box is claimed:
        for box_id in BLACKBOARD.claimed_boxes:
            if BLACKBOARD.claimed_boxes[box_id] == self.id_:
                BLACKBOARD.claimed_boxes.pop(box_id)
                break

    def commit_to_request(self, request, box = None):
        log("Agent {} commited to help with a request".format(self.id_), "BDI", False)
        self.intentions = request
        if box is not None:
            log("Agent {} commited to move box {} from area {}".format(self.id_, box, request.area), "BDI", False)
            BLACKBOARD.claimed_boxes[box.id_] = self.id_
        else:
            log("Agent {} commited to move out of area {}".format(self.id_, request.area), "BDI", False)
    
    def goal_qualified(self, goal):
        return not self.beliefs.is_goal_satisfied(goal) and (goal.row, goal.col) not in BLACKBOARD.claimed_goals and (goal.cave is None or goal.cave.is_next_goal(goal, self.beliefs))

    def pick_box(self, goal, list_of_boxes):
        possible_boxes = self.filter_boxes(goal, list_of_boxes)
        return heapq.heappop(possible_boxes)[1]

    def filter_boxes(self, goal, list_of_boxes):           
        possible_boxes = []
        for box in list_of_boxes:
            if box.letter == goal.letter:
                if (box.row,box.col) in LEVEL.goals_by_pos:
                    if self.beliefs.is_goal_satisfied(LEVEL.goals_by_pos[(box.row,box.col)]):
                        continue
                heapq.heappush(possible_boxes, (self.heuristic.h(self.beliefs, (box,goal), self), box))
        if len(possible_boxes) == 0:
            return None
        return possible_boxes
        
    def boxes_of_my_color_not_already_claimed(self):
        result = []
        for box in self.beliefs.boxes.values():
            if box.color == self.color and (box.id_ not in BLACKBOARD.claimed_boxes):
                result.append(box)
        return result

    def bid_box_to_goal(self, goal, box):
        location = (goal.row, goal.col)
        if isinstance(self.heuristic, Heuristic2):
            my_cost = self.heuristic.f(self.beliefs, (box, location), self)
        else:
            my_cost = self.heuristic.f(self.beliefs, (box, location))
        best_cost = my_cost
        best_agent = self
        log("Agent {} is calling for proposals for moving box {} to {}. Own cost: {}".format(self.id_, box, location, my_cost), "CNET", False)
        for agent in self.all_agents:
            if agent.id_ != self.id_:
                new_cost = agent.calculate_proposal(CfpMoveSpecificBoxTo(box, location),best_cost)
                if  new_cost is not None and new_cost <= best_cost:
                    best_cost = new_cost
                    best_agent = agent
        
        for agent in self.all_agents:
            if agent.id_ == self.id_:
                continue
            if agent.id_ == best_agent.id_: 
                agent.accept_proposal(self)
                continue
            agent.reject_proposal()

        return best_agent