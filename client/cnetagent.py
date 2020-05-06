from agent import BDIAgent
from heuristics import Heuristic
from communication.message import Message
from communication.performative import CfpMoveSpecificBoxTo
from communication.contract import Contract
from communication.blackboard import BLACKBOARD
from action import ActionType, ALL_ACTIONS, UnfoldedAction, Action, Dir
from util import log
import random
from strategy import StrategyBestFirst
from state import LEVEL

"""
    This agent should be allocated subgoals after initialisation using add_subgoal.
    Otherwise it will never aim to move boxes onto their goals. 
"""


class CNETAgent(BDIAgent):

    current_proposal = None
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
        if len(self.desires['contracts']) != 0:
            log("Agent {} refused because it is occupied with another contract".format(self.id_), "BIDDING", False)
            return None
        #update current_proposal + return cost or None as refusal
        if isinstance(performative, CfpMoveSpecificBoxTo) and performative.box.color == self.color:            
            cost = self.heuristic.f(self.beliefs, (performative.box,performative.location))
        else:
            return None
        self.current_proposal = {}
        self.current_proposal['performative'] = performative
        self.current_proposal['cost'] = cost
        log("Agent {}: I can do it in {} moves".format(self.id_, cost), "BIDDING", False)
        return cost

    def accept_proposal(self, manager):
        #construct contract from proposal and add to desires
        contract = Contract(manager, self, self.current_proposal['performative'], self.current_proposal['cost'], self.beliefs.g)
        self.desires['contracts'].append(contract)
        log("Agent {} contracted agent {} to {}".format(manager.id_, self.id_,self.current_proposal['performative']), "CNET", False)
        
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
        #Have we succeeded?
        if self.succeeded():
            log("Agent {} succeeded it's task of {}.".format(self.id_, self.intentions), "BDI", False)
            #Remove contract from desire and BB
            if isinstance(self.intentions, Contract):
                BLACKBOARD.remove(self.intentions)
                self.desires['contracts'].pop(0)
            #Remove claim on box and goal on BB, if intention is (box,goal)
            elif self.intentions is not None:
                box, goal = self.intentions
                BLACKBOARD.remove((box,goal))
            #Reset intentions
            self.intentions = None
        
        #Contract has priority if there is one
        if len(self.desires['contracts']) != 0:
            
            #Is contract already the intention -> return
            if self.intentions == self.desires['contracts'][0]:
                return self.intentions
            
            #Did we have another intention we are overwriting -> Update BB
            if self.intentions is not None:
                box, goal = self.intentions
                BLACKBOARD.remove((box,goal))
            
            #Set intention to be the contract
            self.intentions = self.desires['contracts'][0]
            BLACKBOARD.add(self.intentions, self.id_)
            log("Agent {}'s intention is to fulfill Contract to {}".format(self.id_, self.intentions), "BDI", False)
            return self.intentions
        
        #No contract present, 
        if self.intentions is not None:
            return self.intentions
        
        #pick box, goal not already used, Start bidding to find best contractor.  
        random.shuffle(self.desires['goals'])
        for goal in self.desires['goals']:
            if not self.beliefs.is_goal_satisfied(goal) and (goal.row, goal.col) not in BLACKBOARD.claimed_goals:
                for box in self.beliefs.boxes.values():
                    if box.color == self.color and box.letter == goal.letter:
                        my_box = box
                        break 
                location = (goal.row, goal.col)
                my_cost = self.heuristic.f(self.beliefs, (my_box, location))
                best_cost = my_cost
                best_agent = self
                log("Agent {} is calling for proposals for moving box {} to {}. Own cost: {}".format(self.id_, my_box, location, my_cost), "CNET", False)
                for agent in self.all_agents:
                    if agent.id_ != self.id_:
                        new_cost = agent.calculate_proposal(CfpMoveSpecificBoxTo(my_box, location),best_cost)
                        if  new_cost is not None and new_cost <= best_cost:
                            best_cost = new_cost
                            best_agent = agent
                
                for agent in self.all_agents:
                    if agent.id_ == self.id_:
                        continue
                    if agent.id_ == best_agent.id_: 
                        agent.accept_proposal(self)
                        continue
                    agent.reject_proposal()

                if best_agent.id_ == self.id_:
                    self.intentions = (my_box,goal)
                    break

        #update blackboard (Intentions might be None!)
        if self.intentions is None:
            log("Agent {} has no intentions".format(self.id_), "BDI", False)
            if self.id_ in BLACKBOARD.claimed_boxes.values() or self.id_ in BLACKBOARD.claimed_goals.values():
                raise RuntimeError("Agent has no intentions but is still on the blackboard.")
        else:
            log("Agent {} now has intentions to move box {} to goal {}".format(self.id_, self.intentions[0], self.intentions[1]), "BDI", False)
            BLACKBOARD.add(self.intentions, self.id_)
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
        if self.intentions is None:
            super().plan()
            return
        elif isinstance(self.intentions, Contract):
            box = self.intentions.performative.box
            location = self.intentions.performative.location           
        else:
            box, location = self.intentions       
        plan = self.single_agent_search(self.heuristic, (box, location))
        if len(plan) == 0:
            raise RuntimeError("Empty plan returned from SingleAgentSearch. Agent: {}, Intentions: {}".format(self.id_, self.intentions))
        return 

    """
        Q:  Has something happened in the environment that means I should reconsider my current plan?
            Has somebody entered a "one-person" passage and is now in the way.
            Maybe an alternative route opened up that might be more beneficial to take.
    """
    def reconsider(self) -> 'Bool':
        return self.succeeded()

    """
        Is something/someone blocking my way? Did someone move the block I was going for?
        Q:  How far ahead should we look when deciding if the plan is still feasible
    """
    def impossible(self) -> 'Bool':
        action = self.current_plan[0] #Unfoldedaction
        if action.action.action_type == ActionType.NoOp:
            return False
        #required_free still free?
        if not(self.beliefs.is_free(*action.required_free)):
            return True
        if action.box_from is not None:
            if not(action.box_from in self.beliefs.boxes and self.beliefs.boxes[action.box_from].color == self.color):
                return True 
        return False

    def succeeded(self) -> 'Bool':
        if self.intentions is None:
            return True
        if isinstance(self.intentions, Contract):
            box = self.intentions.performative.box
            location = self.intentions.performative.location 
            if location in self.beliefs.boxes and self.beliefs.boxes[location].id_ == box.id_:
                return True
            return False
        return self.beliefs.is_goal_satisfied(self.intentions[1])  
            
        # If intention box/goal: check if a box is on the goal
        # If intention is Contract: Check is contract os fulfilled or have become void
            #If contract is completed, tell the corresponding agent
        # raise NotImplementedError
    # endregion

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

    # region String representations
    def __repr__(self):
        return str(self.color) + " CNET-Agent with id " + str(self.id_) + " at position " + str((self.row, self.col))

    def __str__(self):
        return self.__repr__()
    # endregion


        

