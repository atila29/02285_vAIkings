from agent.bdiagent import BDIAgent
from action import UnfoldedAction, Action, ActionType, Dir
from heuristics import Heuristic
from communication.blackboard import BLACKBOARD
from communication.contract import Contract
from logger import log

"""
    "Interface" for implementation of CNET Agent
    
    Requires BLACKBOARD implementation
"""


class CNETAgent(BDIAgent):

    
    # region Init
    def __init__(self,
                 id_,
                 color,
                 row,
                 col,
                 initial_beliefs,
                 all_agents,
                 depth=1,
                 heuristic=None):

        self.n = depth
        if heuristic is not None:
            self.heuristic = heuristic
        else:
            self.heuristic = Heuristic(self)

        self.all_agents = all_agents

        # init desires
        self.desires = {}
        self.desires['goals'] = []
        self.desires['contracts'] = []

        self.intentions = None
        self.current_proposal = None

        super().__init__(id_, color, row, col, initial_beliefs)

    # endregion

    # region FIPA/ACL/CNET
    """
        Types of messages to receive:
            request for proposal
            proposal
            refusal
            update on contract: inform/failure
    """


# region Receiving
    """
        return propose/refuse
    """
    def calculate_proposal(self, performative, cost):
        #search for solution to the problem
        #update current_proposal + return cost or None as refusal
        return None

    def accept_proposal(self, manager):
        #construct contract from proposal and add to desires
        contract = Contract(manager, self, self.current_proposal['performative'], self.current_proposal['cost'], self.beliefs.g)
        self.desires['contracts'].append(contract)
        log("Agent {} contracted agent {} to {}".format(manager.id_, self.id_,self.current_proposal['performative']), "CNET", False)
        #Remove current intentions
        self.remove_intentions_from_blackboard()
        self.intentions = contract
        self.add_intentions_to_blackboard()
        return contract

    def reject_proposal(self):
        self.current_proposal = None

    def conclude_contract(self, contract, bool):
        if bool:
            #contract is completed
            pass
        else:
            #couldn't fulfill contract
            pass
# endregion


    # endregion

    def remove_intentions_from_blackboard(self):
        pass

    def add_intentions_to_blackboard(self):
        pass
        
    # region String representations
    def __repr__(self):
        return str(self.color) + " CNET-Agent with id " + str(self.id_) + " at position " + str((self.row, self.col))

    def __str__(self):
        return self.__repr__()
    # endregion

