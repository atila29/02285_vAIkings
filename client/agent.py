from action import ActionType, ALL_ACTIONS, UnfoldedAction, Action, Dir

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




