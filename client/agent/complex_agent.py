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
from action import ActionType, UnfoldedAction, Action, Dir
from cave import Cave
from passage import Passage
from level import AgentElement, AgentGoal
import random

class Trigger:
    name: str

    EMPTY_PLAN = SUCCEDED = IMPOSSIBLE = RECONSIDER = NEW_INTENTIONS = NEXT_MOVE_IMPOSSIBLE = ALL_GOOD = WAITING_FOR_REQUEST = ABOUT_ENTER_CAVE_OR_PASSAGE = None

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()

Trigger.EMPTY_PLAN = Trigger("empty_plan")
Trigger.SUCCEDED = Trigger("succeeded")
Trigger.IMPOSSIBLE = Trigger("impossible")
Trigger.RECONSIDER = Trigger("reconsider")
Trigger.NEW_INTENTIONS = Trigger("new_intentions")
Trigger.NEXT_MOVE_IMPOSSIBLE = Trigger("next_move_impossible")
Trigger.ALL_GOOD = Trigger("all_good")
Trigger.WAITING_FOR_REQUEST = Trigger("waiting_for_request")
Trigger.ABOUT_ENTER_CAVE_OR_PASSAGE = Trigger("about_to_enter_cave_or_passage")


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
        self.desires['end location'] = None

        self.trigger = Trigger.EMPTY_PLAN
        self.plan_for_current_request = None
        self.retreating_duration = 0
        self.all_my_goals_satisfied = False

        self.intentions = None

        ConcreteBDIAgent.__init__(self, id_, color, row, col, initial_beliefs)
        
        self.reprioritise_goals()
        self.deliberate()
        self.plan(ignore_all_other_agents=False)




# region Deliberate
    """
        Method inherited from the BDI agent.
        It will be run if one of the following triggers:
            (trigger = Trigger.EMPTY_PLAN):   The agents current plan is empty and needs a new one and should reconsider its intentions
            (trigger = Trigger.SUCCEDED):    The agents current intentions have been fulfilled and needs new intentions
            (trigger = Trigger.IMPOSSIBLE):   The agents current set of intentions have become impossible to fulfill
            (trigger = Trigger.RECONSIDER):   The agent might have an advange in abandonning the current intentions

        OUTPUT: update intentions (and info of intentions on bb)
    """

    def deliberate(self):
        self.test_for_trigger()
        log("Agent {} is deliberating because {}".format(self.id_, self.trigger), "BDI", False)
        if self.trigger in [Trigger.SUCCEDED, Trigger.IMPOSSIBLE, Trigger.RECONSIDER]:
            if self.succeeded() and isinstance(self.intentions, AgentGoal):
                if self.id_ in BLACKBOARD.claimed_caves:
                    BLACKBOARD.claimed_caves.pop(self.id_)
                if self.id_ in BLACKBOARD.claimed_passages:
                    BLACKBOARD.claimed_passages.pop(self.id_)
            self.remove_intentions_from_blackboard()
            # TODO: remove also resets intentions, change!

        elif self.trigger == Trigger.EMPTY_PLAN:
            if self.succeeded():
                self.all_my_goals_satisfied = self.check_if_all_my_goals_are_satisfied()
                if self.all_my_goals_satisfied:
                     #TODO: what if we destroy a goal at some point?
                     log("Agent {} thinks it is done with all its goals".format(self.id_), "AGENT_GOALS", False)
                self.remove_intentions_from_blackboard()
            elif self.impossible():
                self.remove_intentions_from_blackboard()
            # Keep intentions and go to plan
            else:
                return self.intentions

        if self.intentions is None:
            self.pick_intentions_from_scratch()
            self.trigger = Trigger.NEW_INTENTIONS

        return self.intentions

    def test_for_trigger(self):
        if len(self.current_plan) == 0:
            self.trigger = Trigger.EMPTY_PLAN
        elif self.succeeded():
            self.trigger = Trigger.SUCCEDED
        elif self.impossible():
            self.trigger = Trigger.IMPOSSIBLE
        elif self.reconsider():
            self.trigger = Trigger.RECONSIDER
        
    def check_if_all_my_goals_are_satisfied(self):
        for goal in self.desires['goals']:
            if not self.beliefs.is_goal_satisfied(goal):
                return False
        return True
        

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
            self.current_plan = self.plan_for_current_request
            if len(self.current_plan) > 0:
                self.current_plan.append(UnfoldedAction(Action(ActionType.NoOp,Dir.N, None), self.id_,True, self.current_plan[-1].agent_to))
            return

        # check for contract
        if len(self.desires['contracts']) > 0:
            self.intentions = self.desires['contracts'][0]
            self.add_intentions_to_blackboard()
            log("Agent {} commited to contract {}".format(self.id_, self.intentions), "BDI", False)
            return

        # check for box and goal
        if not self.all_my_goals_satisfied:
            box, goal = self.look_for_box_and_goal()
            if not (box is None or goal is None):
                self.intentions = (box, goal)
                self.add_intentions_to_blackboard()
                log("Agent {} now has intentions to move box {} to goal {}".format(
                    self.id_, self.intentions[0], self.intentions[1]), "BDI", False)
                if self.goal_in_cave(goal):
                    self.clear_cave_until_location((goal.row, goal.col), pair=(box,goal))
                if self.wrong_box_on_goal(goal):
                    self.clear_goal(goal, pair=(box,goal))
                return
        
        elif self.desires['end location'] is not None:
            log("Agent {} have intentions to move to end location. desires: {}".format(self.id_, self.desires['end location']), "AGENT_GOALS", False)
            agent_goal = self.desires['end location']
            if agent_goal.cave is not None:
                if agent_goal.cave.is_next_goal(agent_goal, self.beliefs):
                    self.intentions = self.desires['end location']
                    return
            else:
                self.intentions = self.desires['end location']
                return

        

        # Else pick None
        self.intentions = None
        log("Agent {} has no intentions".format(self.id_), "BDI", False)

    def wrong_box_on_goal(self, goal):
        if (goal.row, goal.col) in self.beliefs.boxes and self.beliefs.boxes[(goal.row, goal.col)].letter != goal.letter:
            return True

    def clear_goal(self, goal, pair=None):
        area_required = [(goal.row, goal.col)]
        request = Request(self.id_, area_required)
        if pair is not None:
            request.purpose = pair
        BLACKBOARD.add(input=request, agent_id = self.id_)
    
    def goal_in_cave(self, goal):
        return LEVEL.map_of_caves[goal.row][goal.col] is not None
                    
    def clear_cave_until_location(self, location, pair=None):
        row,col = location
        for c in LEVEL.map_of_caves[row][col]:
            cave = c
        
        end = len(cave.locations)
        for i in range(len(cave.locations)):
            if cave.locations[i] == location:
                end = i
                break

        area_required = [cave.entrance] + cave.locations[end:]
        request = Request(self.id_, area_required)
        if pair is not None:
            request.purpose = pair
        BLACKBOARD.add(input=request, agent_id = self.id_)

    def check_for_request_to_fulfill(self):
        boxes = self.boxes_of_my_color_not_already_claimed()

        requests = []
        for elm in BLACKBOARD.requests.values():
            for request in elm:
                if self.id_ not in request.agents_that_have_checked_request_already:
                    if not self.present_in_requests(request):
                        requests.append(request)

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
                        path_to_box = self.find_simple_path((self.row, self.col), location, ignore_all_other_agents = False)
                        if path_to_box is None or len (path_to_box) == 0:
                            path_to_box = self.find_simple_path((self.row, self.col), location, ignore_all_other_agents = True)
                            if path_to_box is None or len (path_to_box) == 0:
                                path_to_box = self.find_simple_path((self.row, self.col), location, ignore_all_other_agents = True, ignore_boxes_of_other_color=True)
                                if path_to_box is None or len (path_to_box) == 0:
                                    continue
                        
                        #otherwise find location to move this box to
                        box_path = self.find_path_to_free_space(location)
                        if box_path is None or len(box_path) == 0:
                            #Couldn't find free spot
                            continue
                        
                        #calculate path cost
                        combined_path = self.convert_paths_to_plan(path_to_box, box_path)
                        log("Agent {}. \n path to box: {}. \n box path: {} \n combined path: {}".format(self.id_, path_to_box, box_path, combined_path), "TEST", False)
                        cost = len(combined_path)

                        if cost < float("inf"):
                            log("Agent {} can help with moving box {} out of the area in {} moves".format(self.id_, state.boxes[location], cost), "REQUESTS_DETAILED", False)
                        
                        # If new best, update
                        if cost < best_cost:
                            best_cost = cost
                            best_box = state.boxes[location]
                            best_request = request
                            #path = combined_path + agent_path
                            path = combined_path
            
            #no box to move in request
            if cost == float("inf"):
                #If agent in area:
                if (self.row, self.col) in area:
                    log("Agent {} at position {} in area {}".format(self.id_, (self.row, self.col), request.area), "REQUESTS_DETAILED", False)
                    agent_path = self.find_path_to_free_space((self.row, self.col))                    
                    if agent_path is None or len(agent_path) == 0:
                        log("Found no path ignoring other agents {}".format(agent_path),"REQUESTS_DETAILED", False)
                        agent_path = self.find_path_to_free_space((self.row, self.col), ignore_all_other_agents=True)
                        if agent_path is not None and len(agent_path)>0:
                            log("Found path ignoring other agents {}".format(agent_path),"REQUESTS_DETAILED", False)
                        else:
                            agent_path = self.find_path_to_free_space((self.row, self.col), ignore_all_other_agents=True, ignore_all_boxes = True)
                            if agent_path is not None and len(agent_path)>0:
                                log("Found path ignoring other agents and boxes: {}".format(agent_path),"REQUESTS_DETAILED", False)
                            else:
                                log("Agent {} found no free space to move to to clear the area in request {}".format(self.id_, request), "REQUESTS_DETAILED", False)
                                request.agents_that_have_checked_request_already.append(self.id_)
                    #calculate cost if plan found
                    if agent_path is not None and len(agent_path) > 0:
                        cost = len(agent_path)

                        # If new best, update
                        if cost < best_cost:
                            best_cost = cost
                            best_request = request
                            path = agent_path
                #agent not in area
                else:
                    log("Agent {} not in area so can't help with request {}".format(self.id_, request), "REQUESTS_DETAILED", False)
                    request.agents_that_have_checked_request_already.append(self.id_)
        #end for 
        
        #No requests to help with
        if best_cost == float("inf"):
            log("Agent {} is unable to help with the requests".format(self.id_), "REQUESTS", False)
            return False, None, None
        else:
            self.plan_for_current_request = path
            log("Agent {} is able to help with the request {} in {} moves.".format(self.id_, best_request, best_cost), "REQUESTS", False)
            return True, best_request, best_box

    # TODO: put priority on goals not in cave/passage!
    def look_for_box_and_goal(self):
        boxes = self.boxes_of_my_color_not_already_claimed()
        # pick box, goal not already used, Start bidding to find best contractor.
        # random.shuffle(self.desires['goals'])
        
        #self.reprioritise_goals()
        
        choices = []
        

        for goal in self.desires['goals']:
            if self.goal_qualified(goal):
                box = self.pick_box(goal, boxes) 
                if box is None:
                    continue
                best_agent = self.bid_box_to_goal(goal, box)

                if best_agent.id_ == self.id_:
                    if self.present_in_requests((box,goal)):
                        continue
                    choices.append((box, goal))
        #No choices
        if len(choices) == 0:
            return None, None

        #pick best choice    
        best_pair = choices[0]
        for box, goal in choices:
            box_location = (box.row, box.col)
            goal_location = (goal.row, goal.col)
            box_cave = None

            if LEVEL.map_of_caves[box.row][box.col] is not None:
                for cave in LEVEL.map_of_caves[box.row][box.col]:
                    if box_location in cave.locations:
                        box_cave = cave
            if box_cave is not None:
                if not self.is_path_to_location_free_in_cave(box_cave, box_location):
                    continue

            if goal.cave is not None:
                if not self.is_path_to_location_free_in_cave(goal.cave, goal_location):
                    continue

            if (not self.beliefs.is_free(goal.row, goal.col)) and goal_location != (self.row, self.col):
                continue

            best_pair = (box,goal)
            break
        
        return best_pair

    def present_in_requests(self, obj):
        if self.id_ in BLACKBOARD.requests:
            for request in BLACKBOARD.requests[self.id_]:
                if type(request.purpose) == type(obj) and request.purpose == obj:
                    return True
        return False 

    def is_path_to_location_free_in_cave(self, cave: Cave, location):
        reversed_cave_locations = cave.locations[::-1]
        for loc in reversed_cave_locations:
            if loc == location:
                return True
            if not self.beliefs.is_free(loc[0], loc[1]):
                return False
        
    #1. caves
    #2. others 
    #3. passages
    def reprioritise_goals(self):
        other = []
        cave_goals = []
        passage_goals = []

        passage_locations = []
        cave_locations = []
        #passage_locations = [p.locations for p in LEVEL.passages.values()]
        for passage in LEVEL.passages.values(): 
            passage_locations = passage_locations+passage.locations 
        
        #utgangspunkt i en liste som inneholder goals som ikke er i caves eller passages 
        for caves in LEVEL.caves.values(): 
            cave_locations = cave_locations + caves.locations  
        
        for location in cave_locations:
            for goal in self.desires['goals']:
                if (goal.row, goal.col) == location:
                    cave_goals.append(goal)

        for location in passage_locations:
            for goal in self.desires['goals']:
                if (goal.row, goal.col) == location:
                    passage_goals.append(goal)       

        for goal in self.desires['goals']:
            if ((goal.row, goal.col) not in passage_locations) and ((goal.row, goal.col) not in cave_locations): 
                other.append(goal) #normal goals 
            
            #if (goal.row, goal.col) in passage_locations: #last
            #    passage_goals.append(goal) #passages
                
            #if (goal.row, goal.col) in cave_locations:  #first
            #    cave_goals.append(goal)
        
        self.desires['goals'] = cave_goals + other + passage_goals
    #endregion    
        


    def reconsider(self):
        return not self.sound() and self.waiting_for_request()

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
            self.retreating_duration = 0
            self.trigger = Trigger.NEXT_MOVE_IMPOSSIBLE
            log("trigger set to {}".format(self.trigger), "trigger", False)
            return False

        if self.retreating_duration > 0:
            self.retreating_duration -= 1
            self.trigger = Trigger.ALL_GOOD
            log("trigger set to {}".format(self.trigger), "trigger", False)
            return True

        # if self.waiting_for_request():
        #     self.trigger = "waiting for request"
        #     log("trigger set to {}".format(self.trigger), "trigger", False)
        #     return False

        if self.is_about_to_enter_cave_or_passage():
            if not self.is_way_clear():
                self.trigger = Trigger.ABOUT_ENTER_CAVE_OR_PASSAGE
                log("trigger set to {}".format(self.trigger), "trigger", False)
                return False


        self.trigger = Trigger.ALL_GOOD
        log("trigger set to {}".format(self.trigger), "trigger", False)
        return True

    def is_way_clear(self):

        if self.have_claims():
            #Assuming that if agents have claims, they are relevant for current action
            log("Agent {} testing claims".format(self.id_), "CLAIM", False)
            if not self.claims_are_sound():
                if self.id_ in BLACKBOARD.claimed_passages:
                    BLACKBOARD.claimed_passages.pop(self.id_)
                if self.id_ in BLACKBOARD.claimed_caves:
                    BLACKBOARD.claimed_caves.pop(self.id_)
                log("Agent {} had non-sound-claims".format(self.id_), "TEST", False)
                return False

        row,col = self.current_plan[0].required_free
        log("Found at location: Caves: {}, passages: {}".format(LEVEL.map_of_caves[row][col], LEVEL.map_of_passages[row][col]), "CP", False)
        clear = self.clear_path_through_passages_and_cave()
        if not clear:
            log("Agent {} waiting. Request clearing of path.".format(self.id_), "PLAN", False)
            log("Agents request on blackboard: {}".format(BLACKBOARD.requests[self.id_]), "PLAN", False)

            return False
        else:
            log("Agent {} thinks path through cave/passage is clear".format(self.id_), "PLAN", False)
            return True

    def waiting_for_request(self):
        return self.id_ in BLACKBOARD.requests

    def update_requests(self):
        if self.id_ in BLACKBOARD.requests:
            # check if request done
            for request in BLACKBOARD.requests[self.id_]:
                
                boxes_in_the_area = []
                agents_in_the_area = []
                done = True
                for location in request.area:
                    if not self.beliefs.is_free(location[0], location[1]):
                        if location in self.beliefs.boxes:
                            elm = self.beliefs.boxes[location]
                            boxes_in_the_area.append(elm.id_)
                            if (elm.id_ in BLACKBOARD.claimed_boxes and BLACKBOARD.claimed_boxes[elm.id_] == self.id_) :
                                continue
                        elif location in self.beliefs.agents:
                            elm = self.beliefs.agents[location]
                            agents_in_the_area.append(elm.id_)
                            if elm.id_ == self.id_:
                                continue
                        else:
                            elm = None
                        log("Agent {} waiting for request {}. Location {} occupied by: {}".format(self.id_, request, location, elm), "TEST", False)
                        done = False
                if done:
                    BLACKBOARD.remove(request, self.id_)
                else:
                    if set(boxes_in_the_area) != set(request.boxes_in_the_area) or set(agents_in_the_area) != set(request.agents_in_the_area):
                        #Request have changed
                        request.boxes_in_the_area = boxes_in_the_area
                        request.agents_in_the_area = agents_in_the_area
                        request.agents_that_have_checked_request_already = []


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
    def plan(self, ignore_all_other_agents=True, move_around_specific_agents=None) -> '[UnfoldedAction, ...]':
        log("Agent {} started planning to achieve: {}. trigger: {}".format(self.id_, self.intentions, self.trigger), "PLAN", False)
        if self.trigger in [Trigger.EMPTY_PLAN, Trigger.NEW_INTENTIONS]:
            
            if isinstance(self.intentions, Request):
                if self.plan_for_current_request is None or len(self.plan_for_current_request):
                    log("Agent {} switched tried plan for request but there was none".format(self.id_), "PLAN", False)
                    self.wait(1)
                    return
                self.current_plan = self.plan_for_current_request
                self.plan_for_current_request = None
                if self.is_next_action_impossible():
                    log("Agent {} switched to plan for request but thinks it isn't sound. plan {}".format(self.id_, self.current_plan), "PLAN", False)
                    self.wait(1)
                    
                else:
                    log("Agent {} switched to plan for request. plan: {}".format(self.id_, self.current_plan), "PLAN", False)
                return

            if isinstance(self.intentions, AgentGoal):
                agent_path = self.find_simple_path(location_from = (self.row, self.col), location_to = (self.intentions.row, self.intentions.col), ignore_all_other_agents = False)
                log("Agent {} wants to move to its end location {}. And found path {}".format(self.id_,  (self.intentions.row, self.intentions.col), agent_path), "PLAN", False)
                if agent_path is None or len(agent_path) == 0:
                    log("Agent {} failed to find a simple path moving around agents and boxes. It will now ignore agents and try again".format(self.id_), "PLAN", False)
                    agent_path = self.find_simple_path(location_from = (self.row, self.col), location_to = (self.intentions.row, self.intentions.col), ignore_all_other_agents = True)
                    if agent_path is None or len(agent_path) == 0:
                        log("Agent {} failed to find a path ignoring agents, and will look for one ignore agents and boxes".format(self.id_), "PLAN", False)
                        agent_path = self.find_simple_path(location_from = (self.row, self.col), location_to = (self.intentions.row, self.intentions.col), ignore_all_other_agents = True, ignore_all_boxes=True)
                        if agent_path is None or len(agent_path) == 0:
                            log("Agent {} failed to find a path at all".format(self.id_), "PLAN", False)
                            self.current_plan = []
                            self.wait(1)
                            return
                self.current_plan = agent_path
                if not self.sound():
                    self.wait(1)
                    log("Agent {} thinks the plan isn't sound, so it will wait one turn".format(self.id_), "PLAN", False)
                return
            
            if self.intentions is None:
                log("Agent {} has no intentions. So it will wait".format(self.id_), "PLAN", False)
                self.current_plan = []
                self.wait(1)
                return
            
            #TODO FULL REPLAN. (Intention not request or None)
            box, location = self.unpack_intentions_to_box_and_location()
            log("Searching for a simple plan to move box {} to location {}".format(box, location), "PLAN", False)
            #TODO: what if they are None
            if box is not None and location is not None:
                simple_plan = self.search_for_simple_plan(self.heuristic, (box,location), ignore_all_other_agents = ignore_all_other_agents, move_around_specific_agents = move_around_specific_agents)
                if simple_plan is not None and len(simple_plan) > 0:
                    self.current_plan = simple_plan
                    if self.sound():
                        log("Agent {} found simple path and is using it".format(self.id_), "PLAN", False)
                        return
                    else: 
                        log("Agent {} found simple path {} but it is not sound. So it is waiting".format(self.current_plan, self.id_), "PLAN", False)
                        self.wait(1)
                        return     
                else:
                    #TODO:
                    log("Agent {} found no simple path. So it is ignoring boxes of another color and agents".format(self.id_), "PLAN", False)
                    #try to ignore boxes and find a path 
                    simple_plan = self.search_for_simple_plan(self.heuristic, (box,location), ignore_all_other_agents = True, ignore_all_boxes = False, ignore_boxes_of_other_color = True)
                    if simple_plan is None or len(simple_plan) == 0:
                        log("Agent {} found no path ignoring boxes of other colors. So it is ignoring all boxes and agents".format(self.id_), "PLAN", False)
                        simple_plan = self.search_for_simple_plan(self.heuristic, (box,location), ignore_all_other_agents = True, ignore_all_boxes = True)
                    if simple_plan is not None and len(simple_plan) > 0:
                        self.current_plan = simple_plan
                        if not self.sound():
                            log("Agent {} found a path but it is not sound. So it is waiting.".format(self.id_), "PLAN", False)
                            self.wait(1)
                        else:
                            log("Agent {} found a path.".format(self.id_), "PLAN", False)
                    else:
                        if len(self.beliefs.agents) == 1:
                            self.current_plan = self.single_agent_search(self.heuristic, self.intentions)
                            log("Agent {} is a solo agent. So doing single agent search".format(self.id_), "PLAN", False)
                            return
                        log("Agent {} could not find a plan at all".format(self.id_), "PLAN", False)
                        
                        #Figure out how to make requests to help
                        self.current_plan = self.single_agent_search(self.heuristic, self.intentions)
                        return
        

        elif self.trigger == "waiting for request":
            log("Agent {} waiting for request.".format(self.id_), "PLAN", False)
            log("Agents request on blackboard: {}".format(BLACKBOARD.requests[self.id_]), "PLAN", False)
            self.wait(1)
            return

        elif self.trigger == Trigger.NEXT_MOVE_IMPOSSIBLE:
            
            #TODO try retreat move
            result, other_agent = self.analyse_situation()
            log("Agent {} analysing the next move thinks it should {}".format(self.id_, result), "PLAN", False)
            if result =="wait":
                self.wait(1)
            elif result =="try retreat":
                if not self.try_to_retreat(other_agent):
                    log("Agent {} couldn't find a retreat move. So it will replan".format(self.id_), "PLAN", False)
                    self.current_plan = []
                    self.trigger = Trigger.EMPTY_PLAN
                    self.plan()  
            elif result =="need to replan":
                log("Agent {} thinks next move is impossible. So it will replan".format(self.id_), "PLAN", False)
                self.current_plan = []
                self.trigger = Trigger.EMPTY_PLAN
                self.plan()   
            elif result =="going around agent":
                pass
            return         

        elif self.trigger ==  Trigger.ABOUT_ENTER_CAVE_OR_PASSAGE:
            self.wait(1)
        else:
            raise RuntimeError("Agent doesn't know why its planning")

    def try_to_retreat(self, other_agent):
        state = self.beliefs
        #path_direction = other_agent.current_plan[1].action.

        blocked_direction = self.close_blocked_dir(state, self.row, self.col, other_agent)
        log("blocked_direction {}".format(blocked_direction), "RETREAT_DETAILED", False)

        #This agent retreat moves
        # possible, direction = self.retreat_is_possible([blocked_direction, path_direction])
        #possible, direction = self.move_is_possible(blocked_direction)

        possible, directions, retreat_type = self.retreat_is_possible(blocked_direction)
        log("possible: {}, directions: {}, retreat_type:{}".format(possible, directions, retreat_type), "RETREAT_DETAILED", False)

        if len(self.current_plan) > 1:
            #TODO add our relative position to the blocked directions. 
            future_action = self.current_plan[1]


        other_blocked_direction = other_agent.close_blocked_dir(state, other_agent.row, other_agent.col, self) + []
        other_possible, other_directions, other_retreat_type = other_agent.retreat_is_possible(other_blocked_direction)

        if possible:            
            if self.lower_priority(other_agent) or not other_possible:
                retreat, duration = self.retreat_move(directions, retreat_type)
                log("Agent {} is doing a retreat move of type {} to make way for agent {}. (Moves: {})".format(self.id_, retreat_type, other_agent.id_, retreat), "RETREAT", False)

                if retreat_type == "move":
                    self.retreating_duration = 1
                else:
                    self.retreating_duration = 2

                self.current_plan =  retreat
                other_agent.wait_at_least(duration)
                return True
        #The other agent retreat moves
        elif other_possible:
            log("Agent {} thinks agent {} can do a retreat move of type {} and will wait".format(self.id_, other_agent.id_, retreat_type), "RETREAT", False)
            # retreat, duration = other_agent.retreat_move(other_directions, other_retreat_type)
            # other_agent.current_plan = retreat 
            # if retreat_type == "move":
            #     self.wait_at_least(2)
            # else:
            #     self.wait_at_least(3) #TODO: 3 or ??
            # return True
        else:
            log("Agent {} couldn't find a retreat move to make way for agent {}".format(self.id_, other_agent.id_), "RETREAT", False)

            area_required = [action.required_free for action in self.current_plan[:5] if action.action.action_type != ActionType.NoOp] +[(self.row, self.col)] 
            request = Request(self.id_, area_required)
            request.purpose = self.intentions
            if not BLACKBOARD.request_is_there(self.id_, request):
                BLACKBOARD.add(request, self.id_)
                log("Agent {} added request ({}) to make agent {} move".format(self.id_,request, other_agent.id_), "ANALYSE", False)
            log("Agent {} is waiting for agent {} to move".format(self.id_, other_agent.id_), "ANALYSE", False)
            
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
        if action.action.action_type == ActionType.NoOp:
            return "", None
        

        # Can/should we do a retreat move?
        rf_loc = action.required_free 
        if rf_loc == (self.row, self.col):
            log("self.id_: {}, rf_loc: {}, (self.row, self.col): {}, action: {}".format(self.id_, rf_loc, (self.row, self.col), action))
            self.current_plan = []
            self.remove_intentions_from_blackboard()
            self.wait(1)
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
                    log("Agent {} (plan: {}) thinks it will crash with agent {} (Plan: {} and is looking for retreat move".format(self.id_, self.current_plan, other_agent.id_, other_agent.current_plan), "ANALYSE", False)
                    return "try retreat", other_agent
                else:
                    if len(other_agent.current_plan) == 0 or other_agent.current_plan[0].action.action_type == ActionType.NoOp or not other_agent.sound():
                        log("Agent {} thinks agent {} is standing still".format(self.id_, other_agent.id_), "ANALYSE", False)
                                
                        #TODO: it is not supposed to update the plan here! fix!
                        #Try to go around:
                        box, location = self.unpack_intentions_to_box_and_location()
                        if box is not None and location is not None:
                            simple_plan = self.search_for_simple_plan(self.heuristic, (box,location), ignore_all_other_agents = False)
                            if simple_plan is not None and len(simple_plan) > 0:
                                self.current_plan = simple_plan
                                if self.sound() and len(self.current_plan) > 1:
                                    log("Agent {} thinks agent {} is standing still but found a path around. Path: {}".format(self.id_, other_agent.id_, self.current_plan), "ANALYSE", False)
                                    return "going around agent", other_agent
                                else:
                                    log("Agent {} thinks agent {} is standing still but path found is not sound. Path: {}".format(self.id_, other_agent.id_, self.current_plan), "ANALYSE", False)
                                
                        #TODO
                        area_required = [action.required_free for action in self.current_plan[:5] if action.action.action_type != ActionType.NoOp] +[(self.row, self.col)] 
                        request = Request(self.id_, area_required)
                        request.purpose = self.intentions
                        #TODO: check if request is there!
                        if not BLACKBOARD.request_is_there(self.id_, request):
                            BLACKBOARD.add(request, self.id_)
                            log("Agent {} added request ({}) to make agent {} move".format(self.id_,request, other_agent.id_), "ANALYSE", False)
                        log("Agent {} is waiting for agent {} to move".format(self.id_, other_agent.id_), "ANALYSE", False)
                        return "wait", None
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
                    #Try to go around, if not possible make request 
                    #TODO: Try to move around
                    
                    box, location = self.unpack_intentions_to_box_and_location()
                    if box is not None and location is not None:
                        simple_plan = self.search_for_simple_plan(self.heuristic, (box,location), ignore_all_other_agents = False)
                        if simple_plan is not None and len(simple_plan) > 0:
                            self.current_plan = simple_plan
                            if self.sound() and len(self.current_plan) > 1:
                                log("Agent {} thinks box is static but found a path around. Path: {}".format(self.id_, self.current_plan), "ANALYSE", False)
                            else:
                                self.wait(1)
                            return "going around box", other_agent
                    area_required = [action.required_free for action in self.current_plan[:5] if action.action.action_type != ActionType.NoOp]
                    request = Request(self.id_, area_required)
                    request.purpose = self.intentions
                    if not BLACKBOARD.request_is_there(self.id_, request): 
                        BLACKBOARD.add(request, self.id_)
                        log("Agent {} added request ({}) to make box {} move".format(self.id_,request, box), "ANALYSE", False)
                    log("Agent {} is waiting for box {} to move".format(self.id_, box), "ANALYSE", False)
                    return "wait", None
        #When do we get here?
        return "need to replan", None  
        


    def unpack_intentions_to_box_and_location(self):
        if self.intentions is None:
            return None, None
        elif isinstance(self.intentions, Contract):
            box = self.intentions.performative.box
            location = self.intentions.performative.location
        elif isinstance(self.intentions, Request) or isinstance(self.intentions, AgentGoal):
            return None, None         
        else:
            box, goal = self.intentions
            location = (goal.row, goal.col)
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

    def find_area(self, cave_or_passage, pair = None):
        if pair is None:
            box, location = self.unpack_intentions_to_box_and_location()

        if isinstance(cave_or_passage, Cave):
            cave = cave_or_passage
            end = None
            for i in range(len(cave.locations)):
                temp = cave.locations[i]
                if temp in self.beliefs.boxes:
                    if box is not None and box == self.beliefs.boxes[temp]:
                        break
                if temp in LEVEL.goals_by_pos:
                    if self.beliefs.is_goal_satisfied(LEVEL.goals_by_pos[temp]):
                        end = i
                        continue
                    if location is not None and temp == location:
                        break
                if temp in self.beliefs.agents and self.beliefs.agents[temp].id_ != self.id_:
                    break 
                end = i
            #clear whole cave
            if end is None:
                area_required = [cave.entrance] + cave.locations
            #clear until end
            else:
                area_required = [cave.entrance] + cave.locations[end+1:]
            
            return area_required

        if isinstance(cave_or_passage, Passage):
            return cave_or_passage.locations + cave_or_passage.entrances

    def goal_qualified(self, goal):
        requests = []
        for elm in BLACKBOARD.requests.values():
            for request in elm:
                if goal ==  request.goal:
                    return False
        return not self.beliefs.is_goal_satisfied(goal) and (goal.row, goal.col) not in BLACKBOARD.claimed_goals and (goal.cave is None or goal.cave.is_next_goal(goal, self.beliefs))


    def wait(self, duration):
        self.wait_at_least(duration)



