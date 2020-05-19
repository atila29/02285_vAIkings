from agent.bdiagent import BDIAgent
from level import AgentElement, Goal
from state import State
from heuristics import SimpleHeuristic, DepthHeuristic, Heuristic2
from action import ActionType, Action, UnfoldedAction, Dir, ALL_MOVE_ACTIONS
from communication.blackboard import BLACKBOARD
from strategy import StrategyBestFirst
from util import reverse_direction
from logger import log


class SearchAgent(BDIAgent):
    """
        returns a list of move action from location_from to location_to
        ignores agents
        moves around all boxes

        Returns None if no path exists
        otherwise returns list of UnfoldedActions (only moves)
    """
    def find_simple_path(self, location_from, location_to, ignore_all_boxes=False, ignore_all_other_agents = True, move_around_specific_agents=None):
        #pretend agent is at location_from, and remove agents, and possible target box 
        state = State(self.beliefs)
        if ignore_all_other_agents:
            state.agents = {}
        elif move_around_specific_agents is not None:
            for pos in state.agents:
                if state.agents[pos].id_ in move_around_specific_agents:
                    continue
                else:
                    state.agents.pop(pos)  
        else:
            #ignore only my self
            state.agents.pop((self.row,self.col))
        state.agents[location_from] = AgentElement(self.id_, self.color, location_from[0], location_from[1])
        
        if ignore_all_boxes:
            state.boxes = {}
        else:
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

    def find_path_to_free_space(self, location, ignore_all_other_agents = False):
        #search from location, find spot not in an area requested free
        #pretend agent is at location_from, and remove agents, and possible target box 
        state = State(self.beliefs)
        if ignore_all_other_agents:
            state.agents = {}
        else:
            state.agents.pop((self.row, self.col))
        state.agents[location] = AgentElement(self.id_, self.color, location[0], location[1])
        if location in state.boxes:
            state.boxes.pop(location)
        
        #define heuritic to be distance from agent to location_to
        requests = []
        for elm in BLACKBOARD.requests.values():
            requests = requests + elm
        log("Agent: {}, Requests: {}".format(self.id_, requests), "PATH_TO_FREE", False)
        h = DepthHeuristic(self.id_, requests)
        return self.best_first_search(h, state)

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

    def search_for_simple_plan(self, heuristic, pair = None,ignore_all_boxes=False, ignore_all_other_agents=True, move_around_specific_agents=None) -> '[UnfoldedAction, ...]':
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
        path1= self.find_simple_path((self.row, self.col), (box_row, box_col), ignore_all_boxes=ignore_all_boxes, ignore_all_other_agents=ignore_all_other_agents, move_around_specific_agents=move_around_specific_agents)
        log("First part of search done for agent {}. path 1: {}".format(self.id_, path1), "SAS", False)
        
        if path1 is None:
            #TODO
            #If we can't find a path to the box we need to figure out how to make one!
            #Find out how to make request! 
            # ideas:
                # 1. If the me/box/goal is in a cave, request that free!
                # 2. Find the path in a level with not boxes, no agents and start moving along that path. 
                        # Request cave/passages free as we get to it.
                # How do we handle big clusters of boxes? Request them free one at a time, or a chunks at a time?

            log("path 1 in search_for_simple_plan was None", "TEST", False)
            return None

        #Search for path from box to goal
        path2 = self.find_simple_path((box_row, box_col), location, ignore_all_boxes=ignore_all_boxes,ignore_all_other_agents=ignore_all_other_agents)
        log("Second part of search done for agent {}. path 2: {}".format(self.id_, path2), "SAS", False)
        
        if path2 is None:
            #TODO
            #Same idea as above
            log("path 2 in search_for_simple_plan was None", "TEST", False)
            return None

        #Convert paths to a plan
        plan = self.convert_paths_to_plan(path1, path2)
        log("Combined and converted paths for agent {}. Result: {}".format(self.id_, plan), "SAS", False)
        
        
        #     #TODO what to do if one of the path doesn't exist? 
        # self.current_plan = plan
        # if not self.beliefs.is_free(*self.current_plan[0].required_free):
        #     #TODO: Handle this better -> e.g. Ask agent to move
        #     self.current_plan.insert(0,UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_))
        # self.sound()
        return plan

    def single_agent_search(self, heuristic, pair = None) -> '[UnfoldedAction, ...]':
        strategy = StrategyBestFirst(heuristic, self)
        #print('Starting search with strategy {}.'.format(strategy), file=sys.stderr, flush=True)
        #ta inn level her ?
        strategy.add_to_frontier(self.beliefs)  # current state
        
        if pair is None:
            box, goal = self.intentions
            location = (goal.row, goal.col)
        else:
            box, location = pair

        self.current_plan =[]
        iterations = 0
        if isinstance(heuristic, Heuristic2):
            next_state = (self.beliefs, heuristic.f(self.beliefs, pair, self))
        else:
            next_state = (self.beliefs, heuristic.f(self.beliefs, pair))
        while True:
            #log("Iteration: " + str(iterations))
            #log("Length of frontier" + str(len(strategy.frontier)))
            iterations = iterations + 1
            #Pick a leaf to explore
            if strategy.frontier_empty() or iterations > 1000:
                #log("frontier is empty")
                break
            leaf = strategy.get_and_remove_leaf()  # 
            
            #If we found solution 
            if leaf.is_box_at_location(location, box.id_):  # if the leaf is a goal stat -> extract plan
                #log("found solution", "info")
                state = leaf  # current state
                while not state.is_current_state(self.beliefs):
                    self.current_plan.append(state.unfolded_action)
                    state = state.parent  # one level up
                self.current_plan.reverse()
                return self.current_plan
           
            #Find agent position in this state
            for agent in leaf.agents.values(): 
                if agent.id_ == self.id_:
                    agent_row = agent.row
                    agent_col = agent.col
            children = leaf.get_children_for_agent(self.id_, agent_row, agent_col)
            for child_state in children:
                if not strategy.is_explored(child_state) and not strategy.in_frontier(child_state):
                    strategy.add_to_frontier(child_state)
                    
                    if isinstance(heuristic, Heuristic2):
                        h = heuristic.f(child_state, pair, self)
                    else:
                        h = heuristic.f(child_state, pair)
                    if h < next_state[1]:
                        next_state = (child_state, h)  
            
            strategy.add_to_explored(leaf)  

        #If no solution found, pick best state in depth n
        #log("didn't find solution")\
        #run through list pick the one with best heuristic
        # state = min(states_in_depth_n, key = lambda state: self.heuristic.f(state))
        state = next_state[0]
        
        #log("Best state in depth n" + str(state))

        if state.is_current_state(self.beliefs):
            self.current_plan = [UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_)]

        #extract plan
        while not state.is_current_state(self.beliefs):
            self.current_plan.append(state.unfolded_action)
            state = state.parent  # one level up
        #log("Extracted plan (in reverse)" + str(self.current_plan))
        #log("Searching done for agent " + str(self.id_) + ", took best state with plan (reversed)" + str(self.current_plan))
        self.current_plan.reverse()
        return self.current_plan
