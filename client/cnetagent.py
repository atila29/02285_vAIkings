from agent import BDIAgent
from heuristics import Heuristic

"""
    This agent should be allocated subgoals after initialisation using add_subgoal.
    Otherwise it will never aim to move boxes onto their goals. 
"""


class CNETAgent(BDIAgent):

    # region Init
    def __init__(self,
                 id_,
                 color,
                 row,
                 col,
                 initial_beliefs,
                 depth=1,
                 heuristic=None):

        super().__init__(id_, color, row, col, initial_beliefs)
        self.n = depth
        if heuristic is not None:
            self.h = heuristic
        else:
            self.heuristic = Heuristic(self)

        # init desires
        self.desires = {}
        self.desires['goals'] = []
        self.desires['contracts'] = []
    # endregion

    # region FIPA/ACL/CNET
    """
        Types of messages to receive:
            request for proposal
            proposal
            refusal
            update on contract: inform/failure
    """
    def receive_message(self, msg):
        raise NotImplementedError

    def calculate_proposal(self, request):
        raise NotImplementedError

    def send_message(self, msg):
        raise NotImplementedError
    # endregion

    # region BDI implementation
    def add_subgoal(self, goal):
        self.desires['goals'].append(goal)

    """
        Q:  Given the desires (goals / contracts) how do we choose the intention? 
            What is most important? -> fulfill contract or satisfy goal?
        Q:  When trying to pick a goal, what should we think about?
            Is another agent already going for this goal?
            How close am I?
        Q:  Given a goal, which box should I try to move?
            Is somebody else trying to move that box - in that case who gets priority? and how do we communicate that?
            How close am I to the box?
            How close is the box to the goal?
            Can I get to the box easily?
            Is there a box that has to be moved anyway because it is in the way of somebody else?
            Does all boxes eventually have to be moved, or do we have a surplus?
    """
    def deliberate(self):
        raise NotImplementedError

    """
        Q:  Given an intention (Contract/goal+box) how do we plan to execute said intention?
        Q:  If the intention is goal+box, how do we search for solution?
            How deep do we search? (is the depth fixed/dynamic)?
            Do we consider the other agents fixed, or should we account for their intentions? (Maybe their intentions/plans are available)
        Q:  Should we try to do it ourself, or ask for help?
            Should they always ask, or only when they can't solve the problem themselves "easily"?
        Q:  What should the agent do when all sub goals are satisfied and they don't have any contracts? 
            i.e. when they don't have any desires.
    """
    def plan(self):
        raise NotImplementedError

    """
        Q:  Has something happened in the environment that means I should reconsider my current plan?
            Has somebody entered a "one-person" passage and is now in the way.
            Maybe an alternative route opened up that might be more beneficial to take.
    """
    def reconsider(self) -> 'Bool':
        raise NotImplementedError

    """
        Is something/someone blocking my way? Did someone move the block I was going for?
        Q:  How far ahead should we look when deciding if the plan is still feasible
    """
    def impossible(self) -> 'Bool':
        raise NotImplementedError

    def succeeded(self) -> 'Bool':
        #If intention box/goal: check if a box is on the goal
        #If intention is Contract: Check is contract os fulfilled or have become void
        raise NotImplementedError
    # endregion

    # region String representations
    def __repr__(self):
        return str(self.color) + " CNET-Agent with id " + str(self.id_) + " at position " + str((self.row, self.col))

    def __str__(self):
        return self.__repr__()
    # endregion
