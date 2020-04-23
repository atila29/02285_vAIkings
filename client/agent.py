from action import ActionType, ALL_ACTIONS, UnfoldedAction, Action, Dir

from util import log
"""
    Basic properties for agents
"""
class Agent:
    color: str  # maybe enums?
    id_: str
    row: int
    col: int

    def __init__(self, id_, color, row, col):
        self.row = row
        self.col = col
        self.color = color
        self.id_ = id_

    def __repr__(self):
        return self.color + " Agent with letter " + self.id_

    def __str__(self):
        return self.id_

"""
    "Interface" for implementation of BDI Agent
"""
class BDIAgent(Agent):

    def __init__(self,
                 id_,
                 color,
                 row,
                 col,
                 initial_beliefs):

        super().__init__(id_, color, row, col)
        self.beliefs = initial_beliefs
        self.deliberate()
        self.current_plan = []


    def brf(self, p):  # belief revision function, return new beliefs (updated in while-loop)
        self.beliefs = p
    
    # Updates desires and intentions 
    def deliberate(self):  
        self.desires = self.options()
        self.intentions = self.filter()

    def options(self) -> '?':  # used in deliberate
        return self.desires

    def filter(self) -> '?':  # used in deliberate
        return self.intentions

    def sound(self) -> 'Bool':  # returns true/false, if sound return true
        return True

    def succeeded(self) -> 'Bool':
        return False

    def impossible(self) -> 'Bool':
        return False

    def reconsider(self) -> 'Bool':
        return True

    #default NoOp plan
    def plan(self) -> '[UnfoldedAction, ...]':
        self.current_plan=[UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_)]
        return self.current_plan

    def get_next_action(self, p) -> 'UnfoldedAction': #p is the perception
        self.brf(p)
        if len(self.current_plan) != 0 and (not self.succeeded()) and (not self.impossible()): 
            if self.reconsider():
                self.deliberate()
            if not(self.sound()):
                self.plan()
        #conflict with other agent,

        elif self.next_to_higher_agent():
            log('in elif sentence')
            log('plan before: ' + str(self.current_plan))
            self.current_plan = self.retreat_move() + self.current_plan
            log('plan after : ' + str(self.current_plan))
            #self.current_plan[:0] = [UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_)]
        else:
            # log("Agent " + str(self.id_) +" at position " + str((self.row, self.col)) + " is replanning because:")
            # if len(self.current_plan) == 0:
            #     log("Length of current plan, was 0")
            # elif self.succeeded():
            #     log("Previous plan succeeded")
            # elif self.impossible:
            #     log("Current plan: " + str(self.current_plan)+ " was impossible")
            self.deliberate()
            self.plan()
        return self.current_plan[0] #what if empty?

    def next_to_agent(self):
        current_state = self.beliefs
        up_agent = current_state.agents.get((self.row - 1, self.col))  # check up
        down_agent = current_state.agents.get((self.row + 1, self.col))
        left_agent = current_state.agents.get((self.row, self.col - 1))
        right_agent = current_state.agents.get((self.row, self.col + 1))
        log('agent: ' + str(self))
        log(up_agent)
        log(down_agent)
        log(left_agent)
        log(right_agent)
        return up_agent, down_agent, left_agent, right_agent


    def next_to_higher_agent(self) -> bool:
        up_agent, down_agent, left_agent, right_agent = self.next_to_agent()
        if up_agent is not None and self.id_ > up_agent.id_:
            return True
        if down_agent is not None and self.id_ > down_agent.id_:
            return True
        if left_agent is not None and self.id_ > left_agent.id_:
            return True
        if right_agent is not None and self.id_ > right_agent.id_:
            return True
        return False

    #assume that the agents does not take into account boxes, flytt opp og ned igjen, og legg til litt venting.
    #assume: no box
    def retreat_move(self):
        current_state = self.beliefs
        NoOp = UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_)
        moves = [NoOp, NoOp]
        if current_state.is_free(self.row-1, self.col): # up   (self, action, agent_id):
            moves = self.get_UnfoldedAction(Action(ActionType.Move, Dir.N, None)) + moves + self.get_UnfoldedAction(Action(ActionType.Move, Dir.S, None))
            log('up')

        elif current_state.is_free(self.row+1, self.col): # down
            log('down')
            moves = self.get_UnfoldedAction(Action(ActionType.Move, Dir.S, None)) + moves + self.get_UnfoldedAction(Action(ActionType.Move, Dir.N, None))

        elif current_state.is_free(self.row, self.col-1): # left
            moves = self.get_UnfoldedAction(Action(ActionType.Move, Dir.W, None)) + moves + self.get_UnfoldedAction(
                Action(ActionType.Move, Dir.E, None))

            log('left')

        elif current_state.is_free(self.row-1, self.col+1): # right
            moves = self.get_UnfoldedAction(Action(ActionType.Move, Dir.E, None)) + moves + self.get_UnfoldedAction(
                Action(ActionType.Move, Dir.W, None))
            log('right')

        else:
            return [UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_)] #wait
        return moves

    #har en action --> UnfoldedAction
    def get_UnfoldedAction(self, action: 'Action') -> []:
        new_agent_row = self.row + action.agent_dir.d_row
        new_agent_col = self.col + action.agent_dir.d_col
        unfolded_action = UnfoldedAction(action, self.id_)
        unfolded_action.agent_from = (self.row, self.col)
        unfolded_action.agent_to = (new_agent_row, new_agent_col)
        unfolded_action.will_become_free = (self.row, self.col)
        unfolded_action.required_free = (new_agent_row, new_agent_col)
        return [unfolded_action]



