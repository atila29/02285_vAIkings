from agent.searchagent import SearchAgent

from communication.blackboard import BLACKBOARD

from action import Action, ActionType, Dir, UnfoldedAction

from util import reverse_direction, is_adjacent
from logger import log

class RetreatAgent(SearchAgent):
    
    def __init__(self,
                 id_,
                 color,
                 row,
                 col,
                 initial_beliefs,
                 all_agents,
                 heuristic=None):

        self.all_agents = all_agents

        super().__init__(id_, color, row, col, initial_beliefs)


    """
    If two agents are going oposite directions 
    """
    def about_to_crash(self, box=None, agent = None):
        my_action = self.current_plan[0]
        if len(agent.current_plan)==0:
            return False
        else:
            other_action = agent.current_plan[0]
        if other_action.action.action_type == ActionType.NoOp:
            return False
        if box is None and agent is None: 
            return True
        if my_action.action.action_type == ActionType.Move or  my_action.action.action_type ==  ActionType.Pull:
            my_dir = my_action.action.agent_dir

        elif my_action.action.action_type == ActionType.Push:
            my_dir = my_action.action.box_dir

        if box is not None: #is moving 
            #agent box direction 
            other_agent_dir = other_action.action.box_dir
            if my_dir == reverse_direction(other_agent_dir): 
                return True
            else: 
                return False

        else:
            other_agent_dir = other_action.action.agent_dir
            if my_dir == reverse_direction(other_agent_dir): 
                return True 
            else: 
                return False


    """
        OUTPUT list of blocked directions 
    """
    def close_blocked_dir(self, state, row, col, other_agent):
        blocked_spaces = []
        for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
            if not state.is_free(row + direction.d_row, col + direction.d_col): 
                blocked_spaces.append(direction)

        if len(other_agent.current_plan) > 1:
            a = other_agent.current_plan[1]
            if a.action.action_type == ActionType.Move or a.action.action_type == ActionType.Pull:
                direction = [a.action.agent_dir]
            else:
                direction = [a.action.box_dir]
        else:
            direction = [] 

        return blocked_spaces + direction

    def move_direction(self, state, row, col, ignore_directions): 
        for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
            if (direction not in ignore_directions) and state.is_free(row + direction.d_row, col + direction.d_col):
                return direction



    """
        OUTPUT list of moves, duration (time it takes for self to clear the space, sent to the other agent) 
    """
    def retreat_move(self, directions, retreat_type, wait_duration=3):
        state = self.beliefs
        NoOp = UnfoldedAction(Action(ActionType.NoOp,Dir.N, None), self.id_,True, (self.row, self.col))
        has_box, pos_box, relative_pos = self.agent_has_box() #True, box, pos, relative_pos
        #is just an agent
        if retreat_type == "move":
            direction = directions[0]
            opposite = reverse_direction(direction)
            retreat_move = UnfoldedAction(Action(ActionType.Move, direction, None), self.id_, True, (self.row, self.col))
            new_location = (self.row + direction.d_row, self.col + direction.d_col)
            NoOp = UnfoldedAction(Action(ActionType.NoOp,Dir.N, None), self.id_,True, new_location)
            back_move = UnfoldedAction(Action(ActionType.Move, opposite, None), self.id_, True, new_location)
            #moves = [retreat_move,NoOp,NoOp,back_move]
            moves=[retreat_move, NoOp]
            return moves, 1
        if retreat_type == "push":
            moves =[]
            #direction = self.current_plan[0].action.agent_dir
            direction = relative_pos #where the box is relative to agent # Ex. box is located north of the agent
            dir1, dir2 = directions[0], directions[1]
            move1 = UnfoldedAction(Action(ActionType.Move, direction, None), self.id_, True, (self.row, self.col)) 
            new_location = (self.row + direction.d_row, self.col + direction.d_col)
            move2 = UnfoldedAction(Action(ActionType.Move, dir1, None), self.id_, True, new_location)

            #convert to push actions
            moves.append(self.convert_move_to_push(move1, dir1))
            moves.append(self.convert_move_to_push(move2, dir2))

            end_location = moves[-1].agent_to

            #wait 2 or 3 depending on other agent have box
            moves = moves +[UnfoldedAction(Action(ActionType.NoOp,Dir.N, None), self.id_,True, end_location)]*wait_duration

            #pull back
            # moves.append(self.invert_move(moves[1]))
            # moves.append(self.invert_move(moves[0]))
            return moves, 2
        if retreat_type == "pull": 
            moves =[]
            #direction = self.current_plan[0].action.agent_dir
            direction = relative_pos #where the box is relative to agent # Ex. box is located north of the agent
            dir1, dir2 = directions[0], directions[1]
            move1 = UnfoldedAction(Action(ActionType.Move, dir1, None), self.id_, True, (self.row, self.col)) 
            new_location = (self.row + dir1.d_row, self.col + dir1.d_col)
            move2 = UnfoldedAction(Action(ActionType.Move, dir2, None), self.id_, True, new_location)

            log("dir1={}, dir2={}, relative_pos={}, move1={}, move2={}".format(dir1, dir2, relative_pos, move1, move2))

            #convert to pull actions
            moves.append(self.convert_move_to_pull(move1, reverse_direction(direction))) #1
            moves.append(self.convert_move_to_pull(move2, dir1)) #2

            end_location = moves[-1].agent_to


            #wait 2 or 3 depending on other agent have box
            moves = moves +[UnfoldedAction(Action(ActionType.NoOp,Dir.N, None), self.id_,True, end_location)]*wait_duration

            #push back
            # moves.append(self.invert_move(moves[1]))
            # moves.append(self.invert_move(moves[0]))
            return moves, 2

        #[RETREAT] Agent 5 is doing a retreat move of type pull to make way for agent 9. (Moves: [Pull(N,W), Pull(N,N), NoOp, NoOp, Push(S,N), Push(S,W)])

        '''
        if has_box:
            #kan vi gjøre pull action?
            pull_possible, pull_action = self.pull_actions_possible()
            if pull_possible:     
    
            push_possible, push_action = self.push_actions_possible()
            #kan vi gjøre push action?
            elif push_action_possible():
            #hvor agenten står, hvor boksen står og hvor vi ikke får lov til å gå.
            #the box goes to its intended position
            #den forrige action ? 
            retreat_move = UnfoldedAction(Action(ActionType.Move, direction, direction), self.id_, True, (self.row, self.col))
            new_location_agent = (self.row + direction.d_row, self.col + direction.d_col)
            new_location_box =  (box.row + direction.d_col, box.col + direction.d_col)
        #the box is going to crash into the other 
        
            moves.append(UnfoldedAction(Action(ActionType.NoOp, None, direction), self.id_))
            row, col = self.row, self.col
            new_location = row + direction.d_row, col + direction.d_col 
            ignore_directions = self.close_blocked_dir + [self.oppsite_direction(direction)] #list of blocked directions
            possible, second_direction = self.retreat_is_possible(self,ignore_directions, new_location) 
            #if possible:
        '''
    def invert_move(self, action):
        if action.action.action_type == ActionType.Push:
            #creat pull action
            move = UnfoldedAction(Action(ActionType.Move, reverse_direction(action.action.agent_dir), None), self.id_, True, action.agent_to)
            return self.convert_move_to_pull(move, action.action.box_dir) #opposite from the box, directions from before
        if action.action.action_type == ActionType.Pull:
            move = UnfoldedAction(Action(ActionType.Move, reverse_direction(action.action.agent_dir), None), self.id_, True, action.agent_to)
            return self.convert_move_to_push(move, reverse_direction(action.action.box_dir)) #opposite from the box, directions from before

    def agent_has_box(self):
        action = self.current_plan[0] #unfolded action
        if action.action.action_type == ActionType.Move:
            return False, None, None

        has_box = False

        #agent can have a box even though it is NoOping
        if action.action.action_type == ActionType.NoOp:
            claimed_boxes = []
            for box_id, agent_id in BLACKBOARD.claimed_boxes.items():
                if self.id_ == agent_id:
                    for box in self.beliefs.boxes.values():
                        if box.id_ == box_id:
                            claimed_boxes.append(box)
                            break
            if len(claimed_boxes) > 0:
                for box in claimed_boxes:
                    if is_adjacent((box.row, box.col), (self.row, self.col)):
                        log("Agent at {} Found box at {}".format((self.row, self.col),(box.row, box.col)), "HAS_BOX", False)
                        has_box = True
                        pos = (box.row, box.col)


        if has_box or action.action.action_type == ActionType.Pull or action.action.action_type == ActionType.Push:
            if not has_box:
                log("Agent {} Using box_from : {}".format((self.row, self.col),action.box_from), "HAS_BOX", False)
                pos = action.box_from
            #box = state.boxes[pos]
            relative_pos = None
            # Ex. box is located north to the agent
            

            if (self.row-1,self.col) == pos:
                relative_pos = Dir.N
            if (self.row+1,self.col) ==pos:
                relative_pos = Dir.S
            if (self.row,self.col-1) == pos:
                relative_pos = Dir.W
            if (self.row,self.col+1) == pos:
                relative_pos = Dir.E
            return True, pos, relative_pos
        else:
            return False, None, None

    """
        wrapper for action_possible methods
    """
    def retreat_is_possible(self, ignore_directions):
        next_action = self.current_plan[0]
        if next_action.action.action_type == ActionType.Move:
            success, action = self.move_action_possible(ignore_directions)
            log("move_action_possible({}) = {}".format(ignore_directions, (success, action)), "RETREAT_DETAILED", False)
            actions = [action]
            retreat_type = "move"
        elif self.agent_has_box()[0]:
            success, actions = self.simple_pull_actions_possible(ignore_directions)
            log("simple_pull_actions_possible({}) = {}".format(ignore_directions, (success, actions)), "RETREAT_DETAILED", False)
            retreat_type = "pull"
            if not success: 
                success, actions = self.simple_push_actions_possible(ignore_directions)
                log("simple_push_actions_possible({}) = {}".format(ignore_directions, (success, actions)), "RETREAT_DETAILED", False)
                retreat_type = "push"
        else:
            success, actions, retreat_type = False, [], "No retreat possible"
        return success, actions, retreat_type

    def wait_at_least(self, least): 
        counter = 0
        for elem in self.current_plan: 
            if elem.action.action_type == ActionType.NoOp:
                counter = counter + 1
            else:
                break
        if counter >= least:
            return
        else:
            self.current_plan = [UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_)]*(least-counter) + self.current_plan
            return 




    """
        returns 2 
    """
    def push_actions_possible(self, box, relative_pos, ignore_directions):
        agent_row, agent_col = self.row, self.col
        agent_dir = None
        box_dir = None
        for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
            if (direction not in ignore_directions) and self.beliefs.is_free(box.row + direction.d_row, box.col + direction.d_col):
                box_dir = direction
                #box is situated north of agent, then agent must go north
                agent_dir = relative_pos
                push_action = UnfoldedAction(Action(ActionType.Push, agent_dir, box_dir), self.id_, True, (self.row, self.col))
                return True, push_action
        return False, None

    def simple_pull_actions_possible(self, ignore_directions, starting_pos = None):
        state = self.beliefs
        if starting_pos is None:
            starting_pos = (self.row, self.col)

        success = False
        #look N, S, E, W of agent and see if we can find two connecting free spots (ignore direction in list)
        for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
            if direction in ignore_directions:
                continue
            if state.is_free(starting_pos[0] + direction.d_row, starting_pos[1] + direction.d_col):
                #look for second free spot (ignore where we came from):
                row, col = starting_pos[0] + direction.d_row, starting_pos[1] + direction.d_col
                dir1 = direction
                for dir2 in [Dir.N, Dir.S, Dir.E, Dir.W]:
                    if dir2 == reverse_direction(dir1):
                        continue
                    if state.is_free(row + dir2.d_row, col + dir2.d_col):
                        success = True
                        return success, [dir1,dir2]
        return False, None
            #TODO: Make pull from dir1, dir2

    def simple_push_actions_possible(self, ignore_directions):
        row, col = self.agent_has_box()[1]
        return self.simple_pull_actions_possible([], starting_pos = (row,col))

    '''
    def pull_actions_possible(self, box, relative_pos, ignore_directions): 
        #close_blocked_dir(state, row, col)
        out_of_the_way = False
        ignore_direction = self.close_blocked_dir(self.beliefs, self.row, self.col)
        state = self.beliefs
        row, col = self.row, self.col
        while ! out_of_the_way: 
            direction = move_direction(row, col)
    
        
            
        
        #box is situated north of agent, then it must go south
        box_dir = reverse_direction(relative_pos)
        if move_is_possible: 
            pull_action = UnfoldedAction(Action(ActionType.Pull, agent_dir, box_dir), self.id_, True, (self.row, self.col))
            return True, pull_action
        return False, None
    '''
    """
        OUTPUT  (True, Dir)
            or
                (False, None)
    """


    def move_action_possible(self,ignore_directions: list, location=None):
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
            if len(agent.current_plan) == 0:
                continue
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
        if other_agent.agent_has_box()[0] and not self.agent_has_box()[0]:
            return True
        return self.id_ < other_agent.id_