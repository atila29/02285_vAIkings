from agent.agent import Agent
from action import UnfoldedAction, Action, ActionType, Dir
from logger import log
"""
    "Interface" for implementation of BDI Agent
"""
class BDIAgent(Agent):

    def __init__(self,
                 id_,
                 color,
                 row,
                 col,
                 initial_beliefs,
                 profiler):

        super().__init__(id_, color, row, col)


        self.profiler = profiler
        self.beliefs = initial_beliefs
        
        self.current_plan = []
        self.deliberate()


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

    ###### BDI control loop ######
    def get_next_action(self, p) -> 'UnfoldedAction':
        self.profiler.start("get_next_action")
        self.brf(p)
        if len(self.current_plan) != 0 and (not self.succeeded()) and (not self.impossible()):
            if self.reconsider():
                self.deliberate()
            if not(self.sound()):
                self.plan()
        
        else:
            self.deliberate()
            self.plan()
        try:
            next_action = self.current_plan[0]
        except IndexError:
            log("This agent does not have a plan")
            log(str(self))
            self.wait(1)
            next_action = self.current_plan[0]
        # TODO: Make sure to check that plan cannot return an empty plan
        self.profiler.stop()
        return next_action
    # endregion

    def wait(self, duration: int):
        self.current_plan = [UnfoldedAction(Action(ActionType.NoOp, Dir.N, Dir.N), self.id_)]*duration + self.current_plan



