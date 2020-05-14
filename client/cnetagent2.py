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
            if isinstance(self.intentions, Request) and len(self.current_plan) > 0:
                return self.intentions
            elif isinstance(self.intentions, Request):
                self.intentions = None
                #TODO update BB
            else:
                return self.intentions
        
        boxes = self.boxes_of_my_color_not_already_claimed()

        # TODO: Look through request, commit to one if any relevant.
        #requests = self.find_relevant_requests()
        requests = []
        for elm in BLACKBOARD.requests.values():
            requests = requests + elm
        #find easiest first
        best_cost, best_request, path = float("inf"), None, None
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
                        log("Agent {}. \n path to box: {}. \n box path: {} \n combined path: {}".format(self.id_, path_to_box, box_path, combined_path))
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
                            best_request = request
                            #path = combined_path + agent_path
                            path = combined_path

            if cost == float("inf"):
                if not request.move_boxes:
                    log("Agent {} found no boxes it was able to move in the request {}".format(self.id_, request), "REQUESTS_DETAILED", False)
                if (self.row, self.col) in area:
                    log("Agent {} in area".format(self.id_))
                    agent_path = self.find_path_to_free_space((self.row, self.col))
                    log("Found path: {}".format(agent_path))
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
            self.intentions = best_request
            #TODO: update blackboard
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
            return super().single_agent_search(heuristic, pair)

        #Search for path from box to goal
        path2 = self.find_simple_path((box_row, box_col), location)
        log("Second part of search done for agent {}. path 2: {}".format(self.id_, path2), "SAS", False)
        
        if path2 is None:
            return super().single_agent_search(heuristic, pair)

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
        if self.id_ in BLACKBOARD.requests:
            #check if request done
            request = BLACKBOARD.requests[self.id_][0]
            for location in request.area:
                if not self.beliefs.is_free(location[0], location[1]):
                    self.wait(1)
                    return True
            BLACKBOARD.remove(request, self.id_)

        next_action = self.current_plan[0]

        if next_action.action.action_type == ActionType.NoOp:
            return True

        wanted_passage = None
        wanted_cave = None

        if len(self.current_plan) > 1:
            future_action =  self.current_plan[1]
            if future_action.action.action_type == ActionType.NoOp:
                return True
            future_location = future_action.required_free
            if LEVEL.map_of_passages[future_location[0]][future_location[1]] is not None:
                wanted_passage = LEVEL.map_of_passages[future_location[0]][future_location[1]][0]
                
            if LEVEL.map_of_caves[future_location[0]][future_location[1]] is not None:
                wanted_cave = LEVEL.map_of_caves[future_location[0]][future_location[1]][0]

        #check if we are trying to move into an occupied passage or cave
        row, col = next_action.required_free
        old_location = next_action.will_become_free
        if LEVEL.map_of_passages[row][col] is not None:
            for passage in LEVEL.map_of_passages[row][col]:
                if (row,col) in passage.entrances:
                    if passage.occupied and (old_location not in passage.locations) and passage == wanted_passage:
                        #log("Agent {} is waiting for passage {} to clear".format(self.id_, passage.id_), "CLEARING", False)
                        #TODO: Make request to clear wanted_passage
                        
                        area_required = passage.locations + passage.entrances
                        request = Request(self.id_, area_required)
                        BLACKBOARD.add(request, self.id_)

                        self.wait(1)
                        return True
                    elif passage == wanted_passage:
                        #TODO: Make this into a function that can be called recursively
                        for index in range(1, len(self.current_plan)-1):
                            if self.current_plan[index].required_free in passage.entrances:
                                exit_action = self.current_plan[index + 1]
                                row, col = exit_action.required_free
                                #moving into another passage
                                if LEVEL.map_of_passages[row][col] is not None:
                                   passage2 = LEVEL.map_of_passages[row][col][0]
                                   if passage2.occupied:
                                        log("Agent {} can't move into passage {} since passage {} is occupied".format(self.id_, wanted_passage.id_, passage2.id_), "CLEARING", False) 
                                        #TODO: Make request to clear wanted passage and passage2

                                        area_required = (passage.locations + passage.entrances) + (passage2.locations + passage2.entrances)
                                        request = Request(self.id_, area_required)
                                        BLACKBOARD.add(request, self.id_)

                                        self.wait(1)
                                        return True
                                #moving into a cave
                                elif LEVEL.map_of_caves[row][col] is not None:
                                    cave2 = LEVEL.map_of_caves[row][col][0]
                                    if cave2.occupied:
                                        log("Agent {} can't move into passage {} since cave {} is occupied".format(self.id_, wanted_passage.id_, cave2.id_), "CLEARING", False)
                                        #TODO: Make request to clear wanted passage and cave2
                                        #TODO: Only add needed spaces in cave:
                                        test = len(self.current_plan[index:])-1
                                        locations_needed_in_cave = [cave2.entrance] + cave2.locations[-test:]
                                        area_required = passage.locations + passage.entrances + locations_needed_in_cave
                                        #area_required = (passage.locations + passage.entrances) + (cave2.locations + [cave2.entrance])
                                        request = Request(self.id_, area_required)
                                        BLACKBOARD.add(request, self.id_)
                                        self.wait(1)
                                        return True


                        log("Agent {} has claimed passage {}".format(self.id_, wanted_passage.id_), "CLEARING", False)


        if LEVEL.map_of_caves[row][col] is not None:
            for cave in LEVEL.map_of_caves[row][col]:
                if (row,col) == cave.entrance:
                    if cave.occupied and (old_location not in cave.locations) and cave == wanted_cave:
                        #log("Agent {} is waiting for cave {} to clear".format(self.id_, cave.id_), "CLEARING", False)
                        #TODO: Make request to clear cave
                        end = None
                        #run backwards finding satisfied goal
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
                        # test = len(self.current_plan)-1
                        # locations_needed_in_cave = [cave.entrance] + cave.locations[-test:]
                        # area_required = locations_needed_in_cave
                        request = Request(self.id_, area_required)
                        BLACKBOARD.add(request, self.id_)
                        self.wait(1)
                        return True

        return True

    #TODO: 
    # Question: Should we always only pass one area, or should we be able to pass a list of areas?
        # benefit to multiple areas: The possibility that the agent might still be in the way after clearing the area is smaller. 
            # (otherwise we risk loop were it moves between two areas it needs to clear) 
    # Question: Should we always only pass one box, or should we be able to pass a list of boxes?
        # benefit to multiple boxes: The agent might use the information that it needs to move more boxes, to make a decision about were to put them
            #shallow vs deep storing
    def clear_object_from_area(self, obj, area):
        
        if isinstance(obj, Box):
            pass
        if isinstance(obj, BDIAgent):
            pass
        if isinstance(area, Passage):
            pass
        if isinstance(area, Cave):
            pass

        #Find location to go to
            #Idea 1: find empty cave with no goals and put it there. (decision: Furthest out or in?)
            #Idea 2: just search for first empty space not in the area. Problem: might block another area.
            #Remark: If it is a box, remember to think about space for the agent, and make sure not to block the agent in (so push over pull actions)
                #Remark how thourough we wanna put the box away could depend on other factors: 
                    # Will the box ever be needed? (i.e. does it have a goal)
                    # Does the agent have another important job to go do, or is it just idling?
                    # How much space do we have in general? (i.e. will we need to store multiple boxes away, then we need to push them deep in the cave)

        
        #Calculate plan to move object to chosen location 
            #Idea: find simple paths (reuse code for convert moves to plan)

    def find_path_to_free_space(self, location):
        #search from location, find spot not in an area requested free
        #pretend agent is at location_from, and remove agents, and possible target box 
        state = State(self.beliefs)
        state.agents.pop((self.row, self.col))
        state.agents[location] = AgentElement(self.id_, self.color, location[0], location[1])
        if location in state.boxes:
            state.boxes.pop(location)
        
        #define heuritic to be distance from agent to location_to
        requests = []
        for elm in BLACKBOARD.requests.values():
            requests = requests + elm
        h = DepthHeuristic(self.id_, requests)
        return self.best_first_search(h, state)


    # def find_relevant_requests(self):
    #     #return requests where 
    #         # 1 : the agent is in the area itself
    #         # 2 : there is a box of the agents color in the area    

        
    #     return []

    def wait(self, duration: int):
        self.current_plan = [UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_)]*duration + self.current_plan

