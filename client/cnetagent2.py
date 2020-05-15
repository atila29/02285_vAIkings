from cnetagent import CNETAgent
from strategy import StrategyBestFirst
from heuristics import SimpleHeuristic, DepthHeuristic
from state import State, LEVEL
from level import AgentElement, Goal
from action import ALL_MOVE_ACTIONS, UnfoldedAction, Action, ActionType, Dir
from logger import log
from util import reverse_direction
from passage import Passage
from communication.request import Request
from communication.blackboard import BLACKBOARD
from communication.contract import Contract
import random
from cave import Cave

class CNETAgent2(CNETAgent):
    def deliberate(self):
        #Have we succeeded?
        if self.succeeded():
            self.remove_intentions_from_blackboard()
        
        #If we already have intentions keep them 
        # TODO: it might be smart to abbandon intentions 
        # ... and do something else while we e.g. wait for an area to clea 
        if self.intentions is not None:
            return self.intentions
        
        boxes = self.boxes_of_my_color_not_already_claimed()

        # TODO: Look through request, commit to one if any relevant.
        #requests = self.find_relevant_requests()
        requests = []
        for elm in BLACKBOARD.requests.values():
            requests = requests + elm
        #find easiest first
        best_cost, best_request, best_box, path = float("inf"), None, None, None
        log("Agent {} considering helping the requests.".format(self.id_), "REQUESTS", False)
        state = self.beliefs
        for request in requests:
            cost = float("inf")
            area = request.area
            if request.move_boxes:
                #find boxes in area of my colour
                for location in area:
                    if location in state.boxes and state.boxes[location] in boxes:
                        #if box on goal in cave: leave it:
                        if location in LEVEL.goals_by_pos and state.is_goal_satisfied(LEVEL.goals_by_pos[location]) and LEVEL.map_of_caves[location[0]][location[1]] is not None:
                            continue
                        #If box unreachable: continue
                        path_to_box = self.find_simple_path((self.row, self.col), location)
                        if path_to_box is None:
                            continue
                        #otherwise find location to move this box to
                        box_path = self.find_path_to_free_space(location)
                        if box_path is None or len(box_path) == 0:
                            continue
                        #TODO: consider not converting the path yet, is it heavy?
                        combined_path = self.convert_paths_to_plan(path_to_box, box_path)
                        log("Agent {}. \n path to box: {}. \n box path: {} \n combined path: {}".format(self.id_, path_to_box, box_path, combined_path), "REQUESTS_DETAILED", False )
                        # last_location = combined_path[-1].agent_to
                        # agent_path = self.find_simple_path(last_location, locations[1])
                        # if agent_path is None:
                        #     continue
                        # cost = len(combined_path) + len(agent_path)
                        cost = len(combined_path)
                        
                        if cost < float("inf"):
                            log("Agent {} can help with moving box {} out of the area in {} moves".format(self.id_, state.boxes[location], cost), "REQUESTS_DETAILED", False)
                        #If new best, update
                        if cost < best_cost:
                            best_cost = cost
                            best_box = state.boxes[location]
                            best_request = request
                            #path = combined_path + agent_path
                            path = combined_path

            if cost == float("inf"):
                if not request.move_boxes:
                    log("Agent {} found no boxes it was able to move in the request {}".format(self.id_, request), "REQUESTS_DETAILED", False)
                if (self.row, self.col) in area:
                    log("Agent {} at position {} in area {}".format(self.id_, (self.row, self.col), request.area), "REQUESTS_DETAILED", False)
                    agent_path = self.find_path_to_free_space((self.row, self.col))
                    log("Found path: {}".format(agent_path), "REQUESTS_DETAILED", False)
                    if agent_path is None or len(agent_path) == 0:
                        log("Agent {} found no free space to move to to clear the area in request {}".format(self.id_, request), "REQUESTS_DETAILED", False)
                    else:
                        cost = len(agent_path)
                    
                        #If new best, update
                        if cost < best_cost:
                            best_cost = cost
                            best_request = request
                            path = agent_path
                    if cost == float("inf"):
                        log("Agent {} is unable to help with request {}".format(self.id_, request), "REQUESTS_DETAILED", False)
                    else:
                        log("Agent {} can move out of the area in {} moves".format(self.id_, cost), "REQUESTS_DETAILED", False)
        if best_cost == float("inf"):
            log("Agent {} is unable to help with the requests".format(self.id_), "REQUESTS", False)
        else:
            self.commit_to_request(best_request, best_box)
            log("plan:{}".format(path))
            self.current_plan = path
            log("Agent {} is able to help with the request {} in {} moves.".format(self.id_, best_request, best_cost), "REQUESTS", False)
            return self.intentions   

        #pick box, goal not already used, Start bidding to find best contractor.  
        random.shuffle(self.desires['goals'])
        for goal in self.desires['goals']:
            if self.goal_qualified(goal):
                box = self.pick_box(goal, boxes)
                if box is None:
                    continue
                best_agent = self.bid_box_to_goal(goal, box)
                
                if best_agent.id_ == self.id_:
                    self.intentions = (box,goal)
                    BLACKBOARD.add(self.intentions, self.id_)
                    log("Agent {} now has intentions to move box {} to goal {}".format(self.id_, self.intentions[0], self.intentions[1]), "BDI", False)
                    break

        #update blackboard (Intentions might be None!)
        if self.intentions is None:
            log("Agent {} has no intentions".format(self.id_), "BDI", False)
    
    def commit_to_request(self, request, box = None):
        log("Agent {} commited to help with a request".format(self.id_), "BDI", False)
        self.intentions = request
        if box is not None:
            log("Agent {} commited to move box {} from area {}".format(self.id_, box, request.area))
            BLACKBOARD.claimed_boxes[box.id_] = self.id_
        else:
            log("Agent {} commited to move out of area {}".format(self.id_, request.area))


    def completed_request(self, request):
        log("Agent {} completed its task in helping with a request".format(self.id_), "BDI", False)
        self.intentions = None

        # Remark: Assume only one box is claimed:
        for box_id in BLACKBOARD.claimed_boxes:
            if BLACKBOARD.claimed_boxes[box_id] == self.id_:
                BLACKBOARD.claimed_boxes.pop(box_id)
                break


    """
        returns a list of move action from location_from to location_to
        ignores agents
        moves around all boxes

        Returns None if no path exists
        otherwise returns list of UnfoldedActions (only moves)
    """
    def find_simple_path(self, location_from, location_to):
        #pretend agent is at location_from, and remove agents, and possible target box 
        state = State(self.beliefs)
        state.agents = {}
        state.agents[location_from] = AgentElement(self.id_, self.color, location_from[0], location_from[1])
        if location_from in state.boxes:
            state.boxes.pop(location_from)
        if location_to in state.boxes:
            state.boxes.pop(location_to)
        
        #define heuritic to be distance from agent to location_to
        h = SimpleHeuristic(self.id_, location_to)
        return self.best_first_search(h, state)

    """
        INPUT: two lists of unfolded move actions, 
                Such that the first move in path2 is from the location of the box
                The last move in path1 is moving onto the box
    """
    def convert_paths_to_plan(self, path1, path2, action=ActionType.Push):
        if action != ActionType.Push:
            raise NotImplementedError
        
        result = path1[:-1]
        
        dir1 = path1[-1].action.agent_dir
        dir2 = path2[0].action.agent_dir
        break_point = 0
        turn = None
        #if going back where we came from: start with pull actions
        if dir1 == reverse_direction(dir2):  
            for i in range(1, len(path2)):
                #check if there is room to turn from pull to push
                if self.count_free_spaces(path2[i]) >=3:
                    #change to push
                    turn = self.swicth_from_pull_to_push(path2[i-1], path2[i])
                    result = result + turn
                    break_point = i
                    break
                #otherwise pull one
                next_action = self.convert_move_to_pull(path2[i], path2[i-1].action.agent_dir)
                result.append(next_action)
            #we couldn't turn and should pull onto goal
            if break_point == len(path2)-1 and turn is None:
                last_action = path2[-1]
                location = last_action.agent_to
                for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
                    
                    if direction == reverse_direction(last_action.action.agent_dir):
                        continue
                    row, col = location[0] + direction.d_row, location[1] + direction.d_col
                    if self.beliefs.is_free(row,col):
                        action = Action(ActionType.Move, direction, None)
                        unfolded_action = UnfoldedAction(action, self.id_, True, location)
                        next_action = self.convert_move_to_pull(unfolded_action, last_action.action.agent_dir)
                        result.append(next_action)
                        break
                return result
        else:
            next_action = self.convert_move_to_push(path1[-1], path2[0].action.agent_dir)
            result.append(next_action)    
        for i in range(break_point, len(path2)-1):
            #push
            next_action = self.convert_move_to_push(path2[i], path2[i+1].action.agent_dir)
            result.append(next_action)
        
        # TODO: what if we cannot turn?
        return result
        
        
        
    def convert_move_to_push(self, action: UnfoldedAction, direction: Dir):
        new_action = Action(ActionType.Push, action.action.agent_dir, direction)
        resulting_action = UnfoldedAction(new_action, action.agent_id)
        resulting_action.agent_from = action.agent_from
        resulting_action.agent_to = action.agent_to
        resulting_action.box_from = action.agent_to
        resulting_action.box_to = (action.agent_to[0] + direction.d_row, action.agent_to[1] + direction.d_col)
        resulting_action.required_free = resulting_action.box_to
        resulting_action.will_become_free = resulting_action.agent_to
        return resulting_action

    def convert_move_to_pull(self, action: UnfoldedAction, direction: Dir):
        reversed_direction = reverse_direction(direction)
        new_action = Action(ActionType.Pull, action.action.agent_dir, reversed_direction)
        resulting_action = UnfoldedAction(new_action, action.agent_id)
        resulting_action.agent_from = action.agent_from
        resulting_action.agent_to = action.agent_to
        resulting_action.box_from =(action.agent_from[0] + reversed_direction.d_row, action.agent_from[1] + reversed_direction.d_col)
        resulting_action.box_to = action.agent_from
        resulting_action.required_free = resulting_action.agent_to
        resulting_action.will_become_free = resulting_action.box_from
        return resulting_action

    """
        OUTPUT: list of two unfolded actions, one pull and one push
    """
    def swicth_from_pull_to_push(self, action_before: UnfoldedAction, action_after: UnfoldedAction):
        box_direction = reverse_direction(action_before.action.agent_dir)
        agent_dir = action_after.action.agent_dir
        row, col = action_after.agent_from
        #choose direction
        for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
            if direction == box_direction or direction == agent_dir:
                continue
            new_row = row + direction.d_row
            new_col = col + direction.d_col
            if not (self.beliefs.is_free(new_row, new_col) or (new_row, new_col) in self.beliefs.agents):
                continue
            turn_dir = direction
            break
        
        #pull
        row, col = action_before.agent_to
        act1 = Action(ActionType.Move, turn_dir, None)
        part1 = UnfoldedAction(act1, self.id_, True, (row,col))
        resulting_action1 = self.convert_move_to_pull(part1, action_before.action.agent_dir)

        #push
        new_location =(row+turn_dir.d_row, col+turn_dir.d_col)
        act2= Action(ActionType.Move, reverse_direction(turn_dir), None)
        part2 = UnfoldedAction(act2, self.id_, True, new_location)
        resulting_action2 = self.convert_move_to_push(part2, action_after.action.agent_dir)
        
        return [resulting_action1, resulting_action2]

    def count_free_spaces(self, action):
        row, col = action.agent_from
        total_free = 0
        current_state = self.beliefs
        for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
            new_row = row + direction.d_row
            new_col = col + direction.d_col
            if current_state.is_free(new_row, new_col) or (new_row, new_col) in current_state.agents:
                total_free = total_free + 1
        return total_free

    def single_agent_search(self, heuristic, pair = None) -> '[UnfoldedAction, ...]':
        if pair is None:
            box, goal = self.intentions
            location = (goal.row, goal.col)
        else:
            box, location = pair
        if isinstance(location, Goal):
            location = (location.row, location.col)
        
        #find box location in current state:
        #Find box position in this state
        for b in self.beliefs.boxes.values(): #box = state.boxes[intended_box.id]
            if b.id_ == box.id_:
                box_row = b.row
                box_col = b.col

        log("Starting Single Agent Search. Box from location {} to location {}".format((box.row, box.col), location), "SAS", False)
        #Searh for path from agent to box
        path1= self.find_simple_path((self.row, self.col), (box_row, box_col))
        log("First part of search done for agent {}. path 1: {}".format(self.id_, path1), "SAS", False)
        
        if path1 is None:
            # if LEVEL.map_of_caves[box_row][box_col] is not None:
            #     for cave in LEVEL.map_of_caves[box_row][box_col]:
            #         self.make_request(cave)
            #TODO
            self.wait(1)
            return self.current_plan

        #Search for path from box to goal
        path2 = self.find_simple_path((box_row, box_col), location)
        log("Second part of search done for agent {}. path 2: {}".format(self.id_, path2), "SAS", False)
        
        if path2 is None:
            #TODO
            self.wait(1)
            return self.current_plan

        #Convert paths to a plan
        plan = self.convert_paths_to_plan(path1, path2)
        log("Combined and converted paths for agent {}. Result: {}".format(self.id_, plan), "SAS", False)
        
        
            #TODO what to do if one of the path doesn't exist? 
        self.current_plan = plan
        if not self.beliefs.is_free(*self.current_plan[0].required_free):
            #TODO: Handle this better -> e.g. Ask agent to move
            self.current_plan.insert(0,UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_))
        self.sound()
        return self.current_plan
        
    

    def best_first_search(self, heuristic, initial_state):
        strategy = StrategyBestFirst(heuristic, self)

        strategy.add_to_frontier(initial_state)  # current state
        path = []
        while True:
            #Pick a leaf to explore
            if strategy.frontier_empty():
                #We did not find a solution
                return None
            leaf = strategy.get_and_remove_leaf()  # 
            
            #If we found solution 
            if heuristic.f(leaf) == 0:  # if the leaf is a goal state -> extract plan
                state = leaf  # current state
                while not state.is_current_state(initial_state):
                    path.append(state.unfolded_action)
                    state = state.parent  # one level up
                path.reverse()
                return path
           
            #Find agent position in this state
            for agent in leaf.agents.values(): 
                if agent.id_ == self.id_:
                    agent_row = agent.row
                    agent_col = agent.col
            
            #generate children for agent
            children = leaf.get_children_for_agent(self.id_, agent_row, agent_col, set_of_actions=ALL_MOVE_ACTIONS)
            for child_state in children:
                if not strategy.is_explored(child_state) and not strategy.in_frontier(child_state):
                    strategy.add_to_frontier(child_state) 
            
            #Add to explored
            strategy.add_to_explored(leaf)

    def sound(self):
        #TODO: Check if we are currently waiting for a request, check status. Wait if neccessary
        #If reqeust not done:
            #wait 1

        #REMOVE CLAIMS
        test, cave_or_passage = self.left_claimed_area()
        while test:
            if self.id_ in BLACKBOARD.claimed_passages and cave_or_passage in BLACKBOARD.claimed_passages[self.id_]:
                BLACKBOARD.remove_claim(self.id_, cave_or_passage)
            
            if self.id_ in BLACKBOARD.claimed_caves and cave_or_passage in BLACKBOARD.claimed_caves[self.id_]:
                BLACKBOARD.remove_claim(self.id_, cave_or_passage)
            
            test, cave_or_passage = self.left_claimed_area()

        if self.id_ in BLACKBOARD.requests:
            
            #check if request done
            for request in BLACKBOARD.requests[self.id_]:
                for location in request.area:
                    if not self.beliefs.is_free(location[0], location[1]):
                        log("Agent {} waiting for request".format(self.id_), "TEST", False)
                        self.wait(1)
                        return True
                BLACKBOARD.remove(request, self.id_)

        next_action = self.current_plan[0]



        if self.will_move_block_cave_entrance() or self.will_move_block_passage_entrance():
            log("Agent {} want to enter passage/cave".format(self.id_), "TEST", False)
            if self.have_claims():
                log("Agent {} testing claims".format(self.id_), "TEST", False)
                if self.claims_are_sound():
                    return True
                else:
                    self.wait(1)
                    return True
            
            row,col = next_action.required_free
            log("Found at location: Caves: {}, passages: {}".format(LEVEL.map_of_caves[row][col], LEVEL.map_of_passages[row][col]), "TEST", False)
            clear = self.clear_path_through_passages_and_cave()
            if not clear:
                log("Agent {} waiting. Request clearing of path".format(self.id_), "TEST", False)
                self.wait(1)
            else:
                log("Agent {} thinks path is clear".format(self.id_), "TEST", False)

        return True

    """
        Check the claimed passages and caves. 
        Returns true if they are still free to go through
        Returns False otherwise
    """
    def claims_are_sound(self):
        log("Testing sound claims", "TEST", False)
        #test all claimed passages
        if self.id_ in BLACKBOARD.claimed_passages:
            for passage in BLACKBOARD.claimed_passages[self.id_]:
                if not self.is_free(passage):
                    log("passage {} not free".format(passage), "TEST", False)
                    return False
        
        if self.id_ in BLACKBOARD.claimed_caves:
            for cave in BLACKBOARD.claimed_caves[self.id_]:
                if not self.is_free(cave):
                    log("cave {} not free".format(cave), "TEST", False)
                    return False
        return True


    def have_claims(self):
        log("Testing if agent have claims. result: {}".format(self.id_ in BLACKBOARD.claimed_passages or self.id_ in BLACKBOARD.claimed_caves), "CLAIMS", False)
        return self.id_ in BLACKBOARD.claimed_passages or self.id_ in BLACKBOARD.claimed_caves
    
    def find_path_to_free_space(self, location):
        #search from location, find spot not in an area requested free
        #pretend agent is at location_from, and remove agents, and possible target box 
        state = State(self.beliefs)
        state.agents = {}
        state.agents[location] = AgentElement(self.id_, self.color, location[0], location[1])
        if location in state.boxes:
            state.boxes.pop(location)
        
        #define heuritic to be distance from agent to location_to
        requests = []
        for elm in BLACKBOARD.requests.values():
            requests = requests + elm
        h = DepthHeuristic(self.id_, requests)
        return self.best_first_search(h, state)

    def wait(self, duration: int):
        self.current_plan = [UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_)]*duration + self.current_plan

    def left_claimed_area(self):
        next_action = self.current_plan[0]
        if next_action.required_free is None or next_action.will_become_free is None:
            return (False, None)
        
        #entrance becomes free
            #was in claimed area

        free = next_action.will_become_free
        old_location = next_action.agent_from
        if LEVEL.map_of_caves[free[0]][free[1]] is not None:
            for cave in LEVEL.map_of_caves[free[0]][free[1]]:
                if free == cave.entrance and old_location in cave.locations + [cave.entrance]:
                    if self.id_ in BLACKBOARD.claimed_caves and cave in BLACKBOARD.claimed_caves[self.id_]:
                        return (True, cave)
        if LEVEL.map_of_passages[free[0]][free[1]] is not None:
            for pas in LEVEL.map_of_passages[free[0]][free[1]]:
                if free in pas.entrances and old_location in pas.locations + pas.entrances:
                    if self.id_ in BLACKBOARD.claimed_passages and pas in BLACKBOARD.claimed_passages[self.id_]:
                        return (True, pas)

        # if next_action.action.action_type == ActionType.Move:
        #     if next_action.agent_from in [cave.entrance for cave in LEVEL.caves.values()]:
        #         for cave in 
        # row, col = next_action.will_become_free
        # location = next_action.required_free
        # if LEVEL.map_of_caves[row][col] is not None:
        #     for cave in LEVEL.map_of_caves[row][col]:
        #         if (row,col) in cave.locations+[cave.entrance]:
        #             if location not in cave.locations:
        #                 return (True, cave)
        # if LEVEL.map_of_passages[row][col] is not None:
        #     for pas in LEVEL.map_of_passages[row][col]:
        #         if (row,col) in pas.locations + pas.entrances:
        #             if location not in pas.locations:
        #                 return (True, pas)
        return (False, None)
        #new_action.will_become_free in passage/cave locations and new_action.required_free not in location + entrance

    """
        OUTPUT: True if next part of path is clear (connected passages + cave)
                False otherwise
    """
    def clear_path_through_passages_and_cave(self):
        
        wanted_passages, wanted_cave = self.find_wanted_passages_and_cave()
        log("wanted_passages: {}, wanted_cave: {}".format(wanted_passages, wanted_cave), "TEST", False)

        can_move = True
        for elm, entrance in wanted_passages + wanted_cave:
            if not self.is_free(elm):
                can_move = False
                break
        
        if can_move:
            for elm, entrance in wanted_passages + wanted_cave:
                BLACKBOARD.claim(self.id_, elm)
                #TODO: remove claims somewhere!
            return True
        
        #TODO: Maybe the agent should consider taking another route instead of waiting
        for elm, entrance in wanted_passages + wanted_cave:
            self.make_request(elm)
        
        return False

    def make_request(self, cave_or_passage):

        if isinstance(cave_or_passage, Cave):
            cave = cave_or_passage
            end = None
            for i in range(len(cave.locations)):
                temp = cave.locations[i]
                if temp in LEVEL.goals_by_pos:
                    if not self.beliefs.is_goal_satisfied(LEVEL.goals_by_pos[temp]):
                        break
                    else:
                        end = i
            #clear whole cave
            if end is None:
                area_required = [cave.entrance] + cave.locations
            #clear until end
            else:
                area_required = [cave.entrance] + cave.locations[end+1:]
            
            request = Request(self.id_, area_required)
            BLACKBOARD.add_request(request, self.id_)

        if isinstance(cave_or_passage, Passage):
            request = Request(self.id_, cave_or_passage.locations + cave_or_passage.entrances)
            BLACKBOARD.add_request(request, self.id_)

    #TODO: If we call this when trying to do a request we will probably not be allowed to enter, since the cave/passage will be blocked by the box we wanna move. How do we handle this?
    def is_free(self, cave_or_passage):
        if isinstance(cave_or_passage, Cave):
            cave = cave_or_passage
 
            for agent_id, c in BLACKBOARD.claimed_caves.items():
                if cave in c and agent_id != self.id_:
                    log("Cave {} is not free since it is claimed by another agent".format(cave), "IS_FREE", False)
                    return False
            

            #Start at the end of the cave and look for boxes and goals
            #Cave is marked as not free if:
                # 1: An unsatisfied goal is blocked (behind a box inside the cave, irrelevant if on a goal or not) 
                # 2: A needed box (claimed, or count to see if any spares) is blocked (behind another box inside the cave, irrelevant if on a goal or not )
            end = None

            for i in range(len(cave.locations)):
                temp = cave.locations[i]

                #If on goal, skip if satisfied, otherwise stop:
                if temp in LEVEL.goals_by_pos:
                    if not self.beliefs.is_goal_satisfied(LEVEL.goals_by_pos[temp]):
                        break
                    else:
                        end = i

                #check for box
                elif temp in self.beliefs.boxes:
                    box = self.beliefs.boxes[temp]
                    #These are not allowed to be blocked, so stop
                    if self.box_is_claimed_by_me(box):
                        end = i
                        break
                    elif self.box_is_needed(box) or self.box_is_claimed_by_other(box):
                        end = i - 1 #TODO: CHECK INDEX? 
                        break

            #clear whole cave
            if end is None:
                area_required = [cave.entrance] + cave.locations
            #clear until end
            else:
                area_required = [cave.entrance] + cave.locations[end+1:]
            
            for location in area_required:
                if location in self.beliefs.boxes:
                    if self.beliefs.boxes[location].id_ not in BLACKBOARD.claimed_boxes or BLACKBOARD.claimed_boxes[self.beliefs.boxes[location].id_] != self.id_:
                        box= self.beliefs.boxes[location]
                        log("Cave {} is not free since there is a box in the required area. {} Box with letter {} at: {}, required area: {}".format(cave, box.color, box.letter, location, area_required), "IS_FREE", False)
                        return False
            if cave.occupied:
                if (self.row, self.col) in cave.locations + [cave.entrance]:
                    log("Cave {} is occupied by the agent itself".format(cave), "IS_FREE", False)
                    return True
                else:
                    log("Cave {} (area: {}) is not free since it is occupied by another agent".format(cave_or_passage, cave_or_passage.locations), "IS_FREE", False)
                    return False

        if isinstance(cave_or_passage, Passage):
            for agent_id in BLACKBOARD.claimed_passages:
                if agent_id != self.id_ and cave_or_passage in BLACKBOARD.claimed_passages[agent_id]:
                    log("Passage {} (area: {}) is claimed by another agent (id: {})".format(cave_or_passage, cave_or_passage.locations, agent_id), "IS_FREE", False)
                    return False
            for location in cave_or_passage.locations:
                if location in self.beliefs.boxes:
                    box = self.beliefs.boxes[location]
                    if not self.box_is_claimed_by_me(box):
                        log("Passage {} (area: {}) is blocked by a box. (box: {})".format(cave_or_passage, cave_or_passage.locations, box), "IS_FREE", False)
                        return False
        
            if cave_or_passage.occupied:
                if (self.row, self.col) in cave_or_passage.locations + cave_or_passage.entrances:
                    log("Passage {} is occupied by the agent itself".format(cave_or_passage), "IS_FREE", False)
                    return True
                log("Passage {} (area: {}) is not free since it is occupied by another agent".format(cave_or_passage, cave_or_passage.locations), "IS_FREE", False)
                return False
            
        log("Cave/passage {} is free".format(cave_or_passage), "IS_FREE", False)
        return True
    
    def box_is_needed(self, box):
        
        #count boxes with box.color and box.letter
        box_count = 0
        for b in self.beliefs.boxes.values():
            if b.letter == box.letter and b.color == box.letter:
                box_count += 1
        
        #count goals with letter
        goal_count = len(LEVEL.goals[box.letter])

        if box_count <= goal_count:
            return True
        return False

    def box_is_claimed_by_me(self, box):
        return box.id_ in BLACKBOARD.claimed_boxes and BLACKBOARD.claimed_boxes[box.id_] == self.id_


    def box_is_claimed_by_other(self, box):
        return box.id_ in BLACKBOARD.claimed_boxes and BLACKBOARD.claimed_boxes[box.id_] != self.id_

    def find_wanted_passages_and_cave(self):
        
        wanted_passages = []
        wanted_cave = []

        next_action = self.current_plan[0]
        if self.will_move_block_passage_entrance(next_action):
            
            row, col = next_action.required_free
            
            explored_entrances=[(row,col)]
            passages_to_explore = [(p, (row,col)) for p in LEVEL.map_of_passages[row][col]]
            

            while len(passages_to_explore) > 0:
                log("passages_to_explore: {}".format(passages_to_explore), "TEST", False)
                passage, enter = passages_to_explore.pop()
                #Do I want to enter one of them? -> add to list
                if self.passage_on_path(passage):
                    wanted_passages.append((passage, enter))
                    for entrance in passage.entrances:
                        if entrance in explored_entrances:
                            continue
                        new_passages = [(p,entrance) for p in LEVEL.map_of_passages[entrance[0]][entrance[1]] if p != passage]
                        explored_entrances.append(entrance)
                        passages_to_explore = passages_to_explore + new_passages

        if len(wanted_passages) > 0:
            last_passage, enter = wanted_passages[-1]
            for entrance in last_passage.entrances:
                if entrance == enter:
                    continue
                exit_location = entrance
        else:
            exit_location = next_action.required_free
        caves_to_explore= LEVEL.map_of_caves[exit_location[0]][exit_location[1]]
        if caves_to_explore is not None:
            for cave in caves_to_explore:
                if self.cave_on_path(cave):
                    wanted_cave.append((cave, exit_location))

        if len(wanted_cave) == 0 and len(wanted_passages) > 0:
            #check if the wanted goal is in the last passage
            last_passage, entrance = wanted_passages[-1]
            location = None
            
            #get goal location
            if isinstance(self.intentions, Contract):
                if isinstance(self.intentions.performative, CfpMoveSpecificBoxTo):
                    box = self.intentions.performative.box
                    location = self.intentions.performative.location
                else:
                    raise NotImplementedError("Unrecognized performative")    
            if self.intentions is not None and not isinstance(self.intentions, Request):
                box, goal = self.intentions
                location = (goal.row, goal.col)
            
            #Check if goal in passage
            if location is not None and location in last_passage.locations:
                #create artificial cave
                artificial_cave = Cave(None, location)
                artificial_cave.entrance = entrance
                end = entrance
                for pos in last_passage.locations:
                    if pos == location:
                        break
                    if self.is_adjacent(pos, end):
                        end = pos
                        artificial_cave.locations.insert(1, end)
                        if pos in LEVEL.goals_by_pos:
                            artificial_cave.goals.append(LEVEL.goals_by_pos[pos])    
                artificial_cave.update_status(self.beliefs)
                wanted_cave = [artificial_cave, entrance]
                wanted_passages = wanted_passages[:-1]

        return wanted_passages, wanted_cave
            
            #TODO: find somewhere to do this
            #check if connected passage is free -> set all as occupied and move
            #otherwise make request and wait for finish
                    
    def is_adjacent(self, pos1, pos2):
        for dir in [Dir.N, Dir.S, Dir.E, Dir.W]:
            if pos1[0] + dir.d_row == pos2[0] and pos1[1] + dir.d_col == pos2[1]:
                return True
        return False
             

    def passage_on_path(self, passage):
        for action in self.current_plan:
            if action.required_free in passage.locations:
                return True
        return False

    def cave_on_path(self, cave):
        for action in self.current_plan:
            if action.required_free == cave.locations[-1]:
                return True
        return False


    def will_move_block_passage_entrance(self, next_action = None):
        if next_action is None:
            next_action = self.current_plan[0]
        if next_action.action.action_type == ActionType.NoOp:
            # row, col = next_action.agent_from
            # return LEVEL.map_of_passages[row][col] is not None
            return False
        location = next_action.required_free
        passages_at_location = LEVEL.map_of_passages[location[0]][location[1]]
        if passages_at_location is None:
            return False
        for passage in passages_at_location:
            if location in passage.entrances:
                return True
        return False

    def will_move_block_cave_entrance(self, next_action=None):
        if next_action is None:
            next_action = self.current_plan[0]
        if next_action.action.action_type == ActionType.NoOp:
            #TODO
            return False
        location = next_action.required_free
        caves_at_location = LEVEL.map_of_caves[location[0]][location[1]]
        if caves_at_location is None:
            return False
        for cave in caves_at_location:
            if cave.entrance == location:
                return True 
        return False

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