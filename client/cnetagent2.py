from cnetagent import CNETAgent
from agent import BDIAgent
from strategy import StrategyBestFirst
from heuristics import SimpleHeuristic
from state import State
from level import AgentElement, Goal
from action import ALL_MOVE_ACTIONS, UnfoldedAction, Action, ActionType, Dir
from util import log

class CNETAgent2(CNETAgent):
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
       
        #if going back where we came from: start with pull actions
        if dir1 == self.reverse_direction(dir2):  
            for i in range(1, len(path2)-1):
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
        else:
            next_action = self.convert_move_to_push(path1[-1], path2[0].action.agent_dir)
            result.append(next_action)    
        for i in range(break_point, len(path2)-2):
            #push
            next_action = self.convert_move_to_push(path2[i], path2[i+1].action.agent_dir)
            result.append(next_action)
        
        # TODO: what if we cannot turn?
        return result
        
    def reverse_direction(self, direction):
        if direction == Dir.N:
            return Dir.S
        elif direction == Dir.S:
            return Dir.N
        elif direction == Dir.E:
            return Dir.W
        else:
            return Dir.E
        
        
        
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
        reversed_direction = self.reverse_direction(direction)
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
        box_direction = self.reverse_direction(action_before.action.agent_dir)
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
        act2= Action(ActionType.Move, self.reverse_direction(turn_dir), None)
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

    def get_next_action(self, p) -> 'UnfoldedAction': #p is the perception
        need_to_replan = False
        self.brf(p)

        if len(self.current_plan) == 0:
            log("Length of current plan, was 0", "BDI", False)
            need_to_replan = True
        elif self.succeeded():
            log("Previous plan succeeded", "BDI", False)
            need_to_replan = True
        elif self.impossible():
            log("Current plan: " + str(self.current_plan)+ " was impossible", "BDI", False)
            action = self.current_plan[0]
            # Can/should we do a retreat move?
            try_to_retreat = False
            rf_loc = action.required_free 
            state = self.beliefs
            #Space is occupied
            if not(state.is_free(*rf_loc)):
                #If agent at the position
                #TODO: a more efficient way to find other_agent
                if rf_loc in state.agents:
                    for agent in self.all_agents:
                        if (agent.row, agent.col) == rf_loc:
                            other_agent = agent
                    if self.about_to_crash(agent = other_agent):
                        try_to_retreat = True
                    else:
                        self.wait(1)
                #If box at the location
                if rf_loc in state.boxes:
                    box = state.boxes[rf_loc] #find the box
                    moving, other_agent = self.box_on_the_move(box)
                    if moving:
                        if self.about_to_crash(box = box, agent = other_agent):
                            try_to_retreat = True
                        else:
                            self.wait(1)
                    else:
                        need_to_replan = True

            if try_to_retreat:
            
                # blocked_direction = statisk informasjon (walls - d vi finner i levels) ? 
                # path_direction: Dir.W
                path_direction = self.current_plan[0]

                blocked_direction = self.close_blocked_dir()


                #This agent retreat moves
                # possible, direction = self.retreat_is_possible([blocked_direction, path_direction])
                possible, direction = self.retreat_is_possible(blocked_direction)

                if self.lower_priority(other_agent) and possible:
                    log('trying retreat_move')
                    log(self)
                    log('with direction: ' + str(direction))
                    retreat, duration = self.retreat_move(direction)

                    self.current_plan =  retreat + self.current_plan
                    other_agent.wait(duration)

                #The other agent retreat moves
                elif other_agent.retreat_is_possible([None,None]): #TODO: not None None
                    retreat, duration = other_agent.retreat_move()
                    other_agent.current_plan = retreat + other_agent.current_plan
                    self.wait(duration)
            #self.current_plan[:0] = [UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_)]
            

        else:
            #next action is doable
            if self.reconsider():
                self.deliberate()
            if not(self.sound()):
                self.plan()

        if need_to_replan:
            self.deliberate()
            self.plan()
        return self.current_plan[0] #what if empty?

    """
    If two agents are going oposite directions 
    """
    def about_to_crash(self, box=None, agent = None):
        my_action = self.current_plan[0]
        other_action = agent.current_plan[0]
        if my_action.action.action_type == ActionType.Move or  my_action.action.action_type ==  ActionType.Pull:
            my_dir = my_action.action.agent_dir
    
        elif my_action.action.action_type == ActionType.Push:
            my_dir = my_action.action.box_dir
        
        if box is not None: #is moving 
            #agent box direction 
            other_agent_dir = other_action.action.box_dir
            if my_dir == self.reverse_direction(other_agent_dir): 
                return True
            else: 
                return False
                
        else:
            other_agent_dir = other_action.action.agent_dir
            if my_dir == self.reverse_direction(other_agent_dir): 
                return True 
            else: 
                return False 

    @staticmethod
    def opposite_direction(direction):
        if Dir.N:
            return  Dir.S
        if Dir.S: 
             return  Dir.N
        if Dir.E:
             return  Dir.W
        if Dir.W:
             return  Dir.E
    
    """
        OUTPUT list of blocked directions 
    """
    def close_blocked_dir(self): 
        state = self.beliefs
        row, col = self.row, self.col
        blocked_spaces = []
        for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
            if not state.is_free(row + direction.d_row, col + direction.d_col): 
                blocked_spaces.append(direction)
        return blocked_spaces

    def agent_has_box(self):
        action = self.current_plan[0].action #unfolded action
        if action.action_type == ActionType.Move or action.action_type == ActionType.NoOp:
            return False, False, False, False
        if action.action_type == ActionType.Pull or action.action_type == ActionType.Push:
            pos = action.required_free
            box = state.boxes[pos]
            relative_pos = None
            # Ex. box is located north to the agent
            if (self.row-1,self.col == pos):
                relative_pos = Dir.S
            if (self.row+1,self.col ==pos):
                relative_pos = Dir.N
            if (self.row,self.col-1 == pos):
                relative_pos = Dir.E
            if (self.row,self.col+1 == pos):
                relative_pos = Dir.W
            return True, box, pos, relative_pos

    """
        OUTPUT list of moves, duration (time it takes for self to clear the space, sent to the other agent) 
    """
    def retreat_move(self):
        NoOp = UnfoldedAction(Action(ActionType.NoOp,Dir.N, None), self.id_,True, (self.row, self.col))
        has_box, box, pos_box = self.agent_has_box()
        #is just an agent
        if not has_box:
            move_is_possible, direction = self.retreat_is_possible()
            opposite = self.opposite_direction(direction)
            retreat_move = UnfoldedAction(Action(ActionType.Move, direction, None), self.id_, True, (self.row, self.col))
            new_location = (self.row + direction.d_row, self.col + direction.d_col)
            back_move = UnfoldedAction(Action(ActionType.Move, opposite, None), self.id_, True, new_location)
            moves = [retreat_move,NoOp,NoOp,back_move]
            return moves, len(moves)
        moves =[]
        if has_box:
            #kan vi gjøre pull action?
            possible_pull, pull_action = self.pull_actions_possible()
            moves.append(pull_action)
            while possible_pull:
                possible_pull, moves = self.pull_actions_possible()
                

            #kan vi gjøre push action?
            if push_action_possible():


            #hvor agenten står, hvor boksen står og hvor vi ikke får lov til å gå.
            #the box goes to its intended position
            #den forrige action ? 
            retreat_move = UnfoldedAction(Action(ActionType.Move, direction, direction), self.id_, True, (self.row, self.col))
            new_location_agent = (self.row + direction.d_row, self.col + direction.d_col)
            new_location_box =  (box.row + direction.d_col, box.col + direction.d_col)
        #the box is going to crash into the other 
    '''
            moves.append(UnfoldedAction(Action(ActionType.NoOp, None, direction), self.id_))
            row, col = self.row, self.col
            new_location = row + direction.d_row, col + direction.d_col 
            ignore_directions = self.close_blocked_dir + [self.oppsite_direction(direction)] #list of blocked directions
            possible, second_direction = self.retreat_is_possible(self,ignore_directions, new_location) 
            #if possible:
    '''

    """
        returns 2 
    """
    def pull_action_possible(self, box, relative direction_agent = None, ignore_directions): 
        row, col = self.row, self.col
        agent_dir = None
        box_dir = None
        for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
            if (direction not in ignore_directions) and state.is_free(row + direction.d_row, col + direction.d_col):
                agent_dir = direction
                box_dir = 
                break
        pull_action = UnfoldedAction(Action(ActionType.Pull, agent_dir, box_dir), self.id_, True, (self.row, self.col))
        return True, pull_action

    def pull_actions_possible2(self, ignore_direction, relative_pos): 
        move = []
        original_move = self.current_plan[0].action
        ignore_direction += [original_move.agent_dir]
        move_is_possible, direction = move_is_possible(self, ignore_direction)
        if move_is_possible: 
            move = UnfoldedAction(Action(ActionType.Move, direction, relative_pos), self.id_, True, (self.row, self.col))
            return True, move
        else: 
            return False, None

    """
        OUTPUT  (True, Dir)
            or
                (False, None)
    """
    def move_is_possible(self,ignore_directions: list, location=None):
        state = self.beliefs
        if location is None:
            row, col = self.row, self.col
        else:
            row, col = location
        #TODO: for depth > 1 
        #for depth 1
        for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
            if (direction not in ignore_directions) and state.is_free(row + direction.d_row, col + direction.d_col):
                return True, direction
        return False, None

    """
        OUTPUT:
                (True, Agent)
            or
                (False, None)
    """
    def box_on_the_move(self, box):
        row, col = box.row, box.col
        adjacent_agents = []
        #look for agent in adjacent spots
        for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
            location = (row + direction.d_row, col + direction.d_col)
            if location in self.beliefs.agents:
            #TODO: make more efficient
                for agent in self.all_agents:
                    if (agent.row, agent.col) == location:
                        adjacent_agents.append(agent)
                        #adjacent_agents.append(self.all_agents[location])

        #for each agent check if first action is push or pull
        for agent in adjacent_agents:
            next_action = agent.current_plan[0]
            if next_action.action.action_type == ActionType.Pull or next_action.action.action_type ==  ActionType.Push:
                #check if they are moving the current box
                if next_action.box_from == (row, col):
                    return (True, agent)
        return (False, None)

    def wait(self, duration: int):
        #self.current_plan[:0] = [UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_)]
        self.current_plan = [UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_)]*duration + self.current_plan
        
    
    """
        OUTPUT: True if this agent has lower priority than other_agent
    """
    def lower_priority(self, other_agent):
        return self.id_ < other_agent.id_