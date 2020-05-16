from agent.concrete_bdiagent import ConcreteBDIAgent
from agent.searchagent import SearchAgent
from agent.concrete_cnetagent import ConcreteCNETAgent
from agent.cpagent import CPAgent
from agent.retreat_agent import RetreatAgent

from communication.blackboard import BLACKBOARD
from communication.contract import Contract
from communication.request import Request

from heuristics import Heuristic
from logger import log
from state import LEVEL
from action import ActionType

import random


class ComplexAgent(RetreatAgent, ConcreteBDIAgent, ConcreteCNETAgent, CPAgent):
    color: str  # color of the agent
    id_: str  # agent id
    row: int  # agent row
    col: int  # agent col
    # current proposal in the CNET structure keys: performative, vaules: int (cost)
    current_proposal: dict
    heuristic: "Heuristic"  # heuristic to be used in search
    all_agents: dict  # Dictionary of all agents, key: location TODO: locations change, so this is stupid. Change to list or key as ID
    desires: dict  # Dictionary containing desires. keys: "goals", "contracts"
    # Agents current intentions, type one of: (Box, Goal), Contract, Request
    intentions = None
    current_plan: list  # List of UnfoldedAction
    trigger: str  # last trigger in BDI structure
    # TODO: complete list of variables

    def __init__(self,
                 id_,
                 color,
                 row,
                 col,
                 initial_beliefs,
                 all_agents,
                 heuristic=None):

        if heuristic is not None:
            self.heuristic = heuristic
        else:
            self.heuristic = Heuristic(self)

        self.all_agents = all_agents

        # init desires
        self.desires = {}
        self.desires['goals'] = []
        self.desires['contracts'] = []

        self.trigger = "empty plan"
        self.plan_for_current_request = None
        self.retreating_duration = 0

        self.intentions = None

        ConcreteBDIAgent.__init__(self, id_, color, row, col, initial_beliefs)



# region Deliberate
    """
        Method inherited from the BDI agent.
        It will be run if one of the following triggers:
            (trigger = "empty plan"):   The agents current plan is empty and needs a new one and should reconsider its intentions
            (trigger = "succeeded"):    The agents current intentions have been fulfilled and needs new intentions
            (trigger = "impossible"):   The agents current set of intentions have become impossible to fulfill
            (trigger = "reconsider"):   The agent might have an advange in abandonning the current intentions

        OUTPUT: update intentions (and info of intentions on bb)
    """

    def deliberate(self):
        self.test_for_trigger()
        log("Agent {} is deliberating because {}".format(self.id_, self.trigger), "BDI", False)
        if self.trigger in ["succeeded", "impossible", "reconsider"]:
            self.remove_intentions_from_blackboard()
            # TODO: remove also resets intentions, change!
        elif self.trigger == "empty plan":
            if self.succeeded():
                self.remove_intentions_from_blackboard()
            elif self.impossible():
                self.remove_intentions_from_blackboard()
            # Keep intentions and go to plan
            else:
                return self.intentions

        if self.intentions is None:
            self.pick_intentions_from_scratch()
            self.trigger = "new intentions"

        return self.intentions

    def test_for_trigger(self):
        if len(self.current_plan) == 0:
            self.trigger = "empty plan"
        elif self.succeeded():
            self.trigger = "succeeded"
        elif self.impossible():
            self.trigger = "impossible"
        elif self.reconsider():
            self.trigger = "reconsider"
        

    """
    Intentions can be (in order):
        1. Request
        2. Contract
        3. (Box, Goal)
        4. None
    """
    def pick_intentions_from_scratch(self):

        # check for request
        check, request, box = self.check_for_request_to_fulfill()
        if check:
            self.commit_to_request(request, box)
            log("Agent {} commited to request {}".format(self.id_, self.intentions), "BDI", False)
            return

        # check for contract
        if len(self.desires['contracts']) > 0:
            self.intentions = self.desires['contracts'][0]
            self.add_intentions_to_blackboard()
            log("Agent {} commited to contract {}".format(self.id_, self.intentions), "BDI", False)
            return

        # check for box and goal
        box, goal = self.look_for_box_and_goal()
        if not (box is None or goal is None):
            self.intentions = (box, goal)
            self.add_intentions_to_blackboard()
            log("Agent {} now has intentions to move box {} to goal {}".format(
                self.id_, self.intentions[0], self.intentions[1]), "BDI", False)
            return

        # Else pick None
        self.intentions = None
        log("Agent {} has no intentions".format(self.id_), "BDI", False)
        return

    def check_for_request_to_fulfill(self):
        boxes = self.boxes_of_my_color_not_already_claimed()

        requests = []
        for elm in BLACKBOARD.requests.values():
            requests = requests + elm

        # find easiest first
        best_cost, best_request, best_box, path = float(
            "inf"), None, None, None
        log("Agent {} considering helping the requests.".format(
            self.id_), "REQUESTS", False)
        state = self.beliefs
        for request in requests:
            cost = float("inf")
            area = request.area
            if request.move_boxes:
                # find boxes in area of my colour
                for location in area:
                    if location in state.boxes and state.boxes[location] in boxes:
                        # if box on goal in cave: leave it:
                        if location in LEVEL.goals_by_pos and state.is_goal_satisfied(LEVEL.goals_by_pos[location]) and LEVEL.map_of_caves[location[0]][location[1]] is not None:
                            continue
                        # If box unreachable: continue
                        path_to_box = self.find_simple_path(
                            (self.row, self.col), location)
                        if path_to_box is None:
                            continue
                        # otherwise find location to move this box to
                        box_path = self.find_path_to_free_space(location)
                        if box_path is None or len(box_path) == 0:
                            continue
                        # TODO: consider not converting the path yet, is it heavy?
                        combined_path = self.convert_paths_to_plan(
                            path_to_box, box_path)
                        log("Agent {}. \n path to box: {}. \n box path: {} \n combined path: {}".format(
                            self.id_, path_to_box, box_path, combined_path), "REQUESTS_DETAILED", False)
                        # last_location = combined_path[-1].agent_to
                        # agent_path = self.find_simple_path(last_location, locations[1])
                        # if agent_path is None:
                        #     continue
                        # cost = len(combined_path) + len(agent_path)
                        cost = len(combined_path)

                        if cost < float("inf"):
                            log("Agent {} can help with moving box {} out of the area in {} moves".format(
                                self.id_, state.boxes[location], cost), "REQUESTS_DETAILED", False)
                        # If new best, update
                        if cost < best_cost:
                            best_cost = cost
                            best_box = state.boxes[location]
                            best_request = request
                            #path = combined_path + agent_path
                            path = combined_path

            if cost == float("inf"):
                if not request.move_boxes:
                    log("Agent {} found no boxes it was able to move in the request {}".format(
                        self.id_, request), "REQUESTS_DETAILED", False)
                if (self.row, self.col) in area:
                    log("Agent {} at position {} in area {}".format(
                        self.id_, (self.row, self.col), request.area), "REQUESTS_DETAILED", False)
                    agent_path = self.find_path_to_free_space(
                        (self.row, self.col))
                    log("Found path: {}".format(agent_path),
                        "REQUESTS_DETAILED", False)
                    if agent_path is None or len(agent_path) == 0:
                        log("Agent {} found no free space to move to to clear the area in request {}".format(
                            self.id_, request), "REQUESTS_DETAILED", False)
                    else:
                        cost = len(agent_path)

                        # If new best, update
                        if cost < best_cost:
                            best_cost = cost
                            best_request = request
                            path = agent_path
                    if cost == float("inf"):
                        log("Agent {} is unable to help with request {}".format(
                            self.id_, request), "REQUESTS_DETAILED", False)
                    else:
                        log("Agent {} can move out of the area in {} moves".format(
                            self.id_, cost), "REQUESTS_DETAILED", False)
        if best_cost == float("inf"):
            log("Agent {} is unable to help with the requests".format(
                self.id_), "REQUESTS", False)
            return False, None, None
        else:
            # TODO: how to save this plan?
            self.plan_for_current_request = path
            log("Agent {} is able to help with the request {} in {} moves.".format(
                self.id_, best_request, best_cost), "REQUESTS", False)
            return True, best_request, best_box

    # TODO: put priority on goals not in cave/passage!
    def look_for_box_and_goal(self):
        boxes = self.boxes_of_my_color_not_already_claimed()
        # pick box, goal not already used, Start bidding to find best contractor.
        random.shuffle(self.desires['goals'])
        for goal in self.desires['goals']:
            if self.goal_qualified(goal):
                box = self.pick_box(goal, boxes)
                if box is None:
                    continue
                best_agent = self.bid_box_to_goal(goal, box)

                if best_agent.id_ == self.id_:
                    return (box, goal)
        return None, None
# endregion

# region sound
    """
        Method inherited from the BDI agent.
        It will be run if the agent has a plan.
        purpose: Check if the current plan is still sound wrt the agents current intentions
        We will need to alter our plan if:
            1. Next spot on our path is blocked
            2. We are still waiting for request to be fulfilled
            3. On our way into a passage/cave that is not free
    """

    def sound(self) -> 'Bool':  # returns true/false, if sound return true
        if self.is_next_action_impossible():
            self.trigger = "next move impossible"
            log("trigger set to {}".format(self.trigger), "trigger", False)
            return False

        if self.retreating_duration > 0:
            self.retreating_duration -= 1
            self.trigger = "all good"
            log("trigger set to {}".format(self.trigger), "trigger", False)
            return True

        if self.waiting_for_request():
            self.trigger = "waiting for request"
            log("trigger set to {}".format(self.trigger), "trigger", False)
            return False

        if self.is_about_to_enter_cave_or_passage():
            self.trigger = "about to enter cave or passage"
            log("trigger set to {}".format(self.trigger), "trigger", False)
            return False

        self.trigger = "all good"
        log("trigger set to {}".format(self.trigger), "trigger", False)
        return True

    def waiting_for_request(self):
        return self.id_ in BLACKBOARD.requests

    def update_requests(self):
        if self.id_ in BLACKBOARD.requests:
            # check if request done
            for request in BLACKBOARD.requests[self.id_]:
                done = True
                for location in request.area:
                    if not self.beliefs.is_free(location[0], location[1]):
                        log("Agent {} waiting for request {}".format(
                            self.id_, request), "TEST", False)
                        done = False
                        break
                if done:
                    BLACKBOARD.remove(request, self.id_)


    """
        OUTPUT: return None if no cave/passage otherwise return the cave/passage
    """

    def is_about_to_enter_cave_or_passage(self):
        return self.will_move_block_cave_entrance() or self.will_move_block_passage_entrance()
            
            
        
# endregion


    """
        We will need to alter our plan if:
            1. Next spot on our path is blocked
            2. We are still waiting for request to be fulfilled
            3. On our way into a passage/cave that is not free
            4. Current plan is empty
            5. New intentions
    """
    def plan(self) -> '[UnfoldedAction, ...]':
        log("Agent {} started planning".format(self.id_), "PLAN", False)
        if self.trigger in ["empty plan", "new intentions"]:
            #TODO FULL REPLAN
            box, location = self.unpack_intentions_to_box_and_location()
            #TODO: what if they are None
            if box is not None and location is not None:
                simple_plan = self.search_for_simple_plan(self.heuristic, (box,location))
                if simple_plan is not None and len(simple_plan) > 0:
                    self.current_plan = simple_plan
                    if self.sound():
                        log("Agent {} found simple path and is using it".format(self.id_), "PLAN", False)
                        return
                    else: 
                        self.wait(1)
                        log("Agent {} found simple path but it is not sound. So it is waiting".format(self.id_), "PLAN", False)
                else:
                    #TODO:
                    log("Agent {} found no simple path. So it is waiting".format(self.id_), "PLAN", False)
                    self.wait(1)
            if isinstance(self.intentions, Request):
                if self.plan_for_current_request is None:
                    log("Agent {} switched tried plan for request but there was none".format(self.id_), "PLAN", False)
                    self.wait(1)
                    return
                self.current_plan = self.plan_for_current_request
                self.plan_for_current_request = None
                if not self.sound():
                    log("Agent {} switched to plan for request but thinks it isn't sound".format(self.id_), "PLAN", False)
                    self.wait(1)
                else:
                    log("Agent {} switched to plan for request".format(self.id_), "PLAN", False)
            if self.intentions is None:
                log("Agent {} has no intentions. So it will wait".format(self.id_), "PLAN", False)
                self.wait(1)

        elif self.trigger == "waiting for request":
            log("Agent {} waiting for request".format(self.id_), "PLAN", False)
            self.wait(1)

        elif self.trigger == "next move impossible":
            #TODO try retreat move
            
            result, other_agent = self.analyse_situation()
            log("Agent {} analysing the next move thinks it should {}".format(self.id_, result), "PLAN", False)
            if result =="wait":
                self.wait(1)
            elif result =="try retreat":
                if not self.try_to_retreat(other_agent):
                    log("Agent {} couldn't find a retreat move. So it will replan".format(self.id_), "PLAN", False)
                    self.current_plan = []
                    self.trigger = "empty plan"
                    self.plan()  
            elif result =="need to replan":
                log("Agent {} thinks next move is impossible. So it will replan".format(self.id_), "PLAN", False)
                self.current_plan = []
                self.trigger = "empty plan"
                self.plan()            

        elif self.trigger ==  "about to enter cave or passage":
            
            if self.have_claims():
                #Assuming that if agents have claims, they are relevant for current action
                log("Agent {} testing claims".format(self.id_), "CLAIM", False)
                if not self.claims_are_sound():
                    self.wait(1)
                return 

            row,col = self.current_plan[0].required_free
            log("Found at location: Caves: {}, passages: {}".format(LEVEL.map_of_caves[row][col], LEVEL.map_of_passages[row][col]), "CP", False)
            clear = self.clear_path_through_passages_and_cave()
            if not clear:
                log("Agent {} waiting. Request clearing of path".format(self.id_), "PLAN", False)
                self.wait(1)
            else:
                log("Agent {} thinks path through cave/passage is clear".format(self.id_), "PLAN", False)
        else:
            raise RuntimeError("Agent doesn't know why its planning")

    def try_to_retreat(self, other_agent):
        state = self.beliefs
        #path_direction = other_agent.current_plan[1].action.

        blocked_direction = self.close_blocked_dir(state, self.row, self.col, other_agent)
        log("blocked_direction {}".format(blocked_direction))

        #This agent retreat moves
        # possible, direction = self.retreat_is_possible([blocked_direction, path_direction])
        #possible, direction = self.move_is_possible(blocked_direction)

        possible, directions, retreat_type = self.retreat_is_possible(blocked_direction)
        log("possible: {}, directions: {}, retreat_type:{}".format(possible, directions, retreat_type))

        other_blocked_direction = other_agent.close_blocked_dir(state, other_agent.row, other_agent.col, self)
        other_possible, other_directions, other_retreat_type = other_agent.retreat_is_possible(other_blocked_direction)

        if possible:            
            if self.lower_priority(other_agent) or not other_possible:
                retreat, duration = self.retreat_move(directions, retreat_type)
                log("Agent {} is doing a retreat move of type {} to make way for agent {}. (Moves: {})".format(self.id_, retreat_type, other_agent.id_, retreat), "RETREAT", False)

                self.retreating_duration = 7

                self.current_plan =  retreat + self.current_plan
                other_agent.wait_at_least(duration)
                return True
        #The other agent retreat moves
        elif other_possible:
            log("Agent {} thinks agent {} can do a retreat move of type {} and will wait".format(self.id_, other_agent.id_, retreat_type), "RETREAT", False)
            # retreat, duration = other_agent.retreat_move(directions, retreat_type)
            # other_agent.current_plan = retreat + other_agent.current_plan
            self.wait_at_least(3) #TODO: 3 or ??
            return True
        else:
            log("Agent {} couldn't find a retreat move to make way for agent {}".format(self.id_, other_agent.id_), "RETREAT", False)
            return False
    #self.current_plan[:0] = [UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_)]

    """
        Called when next move is impossible
        Check if 
            1. retreat move is possible
            2. ??
    """
    def analyse_situation(self):
        log("Starting to analyse situation for agent {}".format(self.id_), "ANALYSE", False)
        action = self.current_plan[0]
        # Can/should we do a retreat move?
        rf_loc = action.required_free 
        state = self.beliefs
        
        #Space is occupied
        if not(state.is_free(*rf_loc)):
            #If agent at the position
            #TODO: a more efficient way to find other_agent
            if rf_loc in state.agents:
                log("Agent {} found agent at desired location {}".format(self.id_, rf_loc), "ANALYSE", False)
                for agent in self.all_agents:
                    if (agent.row, agent.col) == rf_loc:
                        other_agent = agent
                if self.about_to_crash(agent = other_agent):
                    log("Agent {} thinks it will crash with agent {} and is looking for retreat move".format(self.id_, other_agent.id_), "ANALYSE", False)
                    return "try retreat", other_agent
                else:
                    if other_agent.current_plan[0].action.action_type == ActionType.NoOp:
                        log("Agent {} thinks agent {} is standing still so it will try to replan".format(self.id_, other_agent.id_), "ANALYSE", False)
                        return "need to replan", None
                    else:
                        log("Agent {} thinks it can wait for agent {} to pass".format(self.id_, other_agent.id_), "ANALYSE", False)
                        return "wait", None
            #If box at the location
            if rf_loc in state.boxes:
                log("Agent {} found box at desired location {}".format(self.id_, rf_loc), "ANALYSE", False)
                box = state.boxes[rf_loc] #find the box
                moving, other_agent = self.box_on_the_move(box)
                if moving:
                    log("Agent {} thinks agent {} is moving the box {}".format(self.id_, other_agent, box), "ANALYSE", False)
                    if self.about_to_crash(box = box, agent = other_agent): 
                        log("Agent {} thinks it will crash with agent {} currently moving the box {}".format(self.id_, other_agent, box), "ANALYSE", False)
                        return "try retreat", other_agent
                    else:
                        return "wait", None
                else:
                    log("Agent {} sees the box {} as static and will try to replan".format(self.id_, box), "ANALYSE", False)
                    return "need to replan", None
        #When do we get here?
        return "need to replan", None  
        


    def unpack_intentions_to_box_and_location(self):
        if self.intentions is None:
            return None, None
        elif isinstance(self.intentions, Contract):
            box = self.intentions.performative.box
            location = self.intentions.performative.location
        elif isinstance(self.intentions, Request):
            return None, None         
        else:
            box, location = self.intentions
        return box, location

# region execute
    def execute_next_action(self):

        self.update_requests()
        self.update_claims()

        return self.current_plan.pop(0)

    def update_claims(self):
        test, cave_or_passage = self.left_claimed_area()
        while test:
            if self.id_ in BLACKBOARD.claimed_passages and cave_or_passage in BLACKBOARD.claimed_passages[self.id_]:
                BLACKBOARD.remove_claim(self.id_, cave_or_passage)

            if self.id_ in BLACKBOARD.claimed_caves and cave_or_passage in BLACKBOARD.claimed_caves[self.id_]:
                BLACKBOARD.remove_claim(self.id_, cave_or_passage)

            test, cave_or_passage = self.left_claimed_area()
# endregion




