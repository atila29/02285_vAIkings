## Source: https://github.com/atila29/02285_warmup/blob/master/searchclient_python/searchclient/action.py


import sys
from util import log

# Copied from Warmup assignment
class Dir:
    N = S = E = W = None

    def __init__(self, name: 'str', d_row: 'int', d_col: 'int'):
        '''
        For internal use; do not instantiate.
        Use Dir.N, Dir.S, Dir.E, and Dir.W instead.
        '''
        self.name = name
        self.d_row = d_row
        self.d_col = d_col

    def __repr__(self):
        return self.name


Dir.N = Dir('N', -1,  0)
Dir.S = Dir('S',  1,  0)
Dir.E = Dir('E',  0,  1)
Dir.W = Dir('W',  0, -1)


# Copied from Warmup assignment
class ActionType:
    NoOp = Move = Push = Pull = None

    def __init__(self, name: 'str'):
        '''
        For internal use; do not instantiate.
        Use ActionType.Move, ActionType.Push, and ActionType.Pull instead.
        '''
        self.name = name

    def __repr__(self):
        return self.name

    #def __eq__(self, other):
    #    return self.name == other.name


ActionType.Move = ActionType('Move')
ActionType.Push = ActionType('Push')
ActionType.Pull = ActionType('Pull')
ActionType.NoOp = ActionType('NoOp')


# generate list of all grounded actions: 4 moves, 12 push (16 if we count switching places which is never allowed), 12 pull (16 if we count switching places which is never allowed)
class Action:

    def __init__(self, action_type: 'ActionType', agent_dir: 'Dir', box_dir: 'Dir'):
        '''
        For internal use; do not instantiate.
        Iterate over ALL_ACTIONS instead.
        '''
        self.action_type = action_type
        self.agent_dir = agent_dir
        self.box_dir = box_dir
        if action_type == ActionType.NoOp:
            self._repr = '{}'.format(action_type)
        elif box_dir is not None:
            self._repr = '{}({},{})'.format(action_type, agent_dir, box_dir)
        else:
            self._repr = '{}({})'.format(action_type, agent_dir)

    def __repr__(self):
        return self._repr

    def __str__(self):
        return self._repr

    def __eq__(self, other):
        return (self.action_type == other.action_type) and (self.agent_dir == other.agent_dir) and (self.box_dir == other.box_dir)

# Grounded actions.
ALL_ACTIONS = []
ALL_ACTIONS.append(Action(ActionType.NoOp, Dir.N, Dir.N))
for agent_dir in (Dir.N, Dir.S, Dir.E, Dir.W):
    ALL_ACTIONS.append(Action(ActionType.Move, agent_dir, None))
    for box_dir in (Dir.N, Dir.S, Dir.E, Dir.W):
        if agent_dir.d_row + box_dir.d_row != 0 or agent_dir.d_col + box_dir.d_col != 0:
            # If not opposite directions.
            ALL_ACTIONS.append(Action(ActionType.Push, agent_dir, box_dir))
        if agent_dir is not box_dir:
            # If not same directions.
            ALL_ACTIONS.append(Action(ActionType.Pull, agent_dir, box_dir))


class UnfoldedAction:

    def __init__(self, action, agent_id, auto_create=False, location = None):

        self.action = action
        self.agent_id = agent_id
        if auto_create:
            #use agents current position
            if location is None:
                raise RuntimeError("Have to pass location to auto create UnfoldedAction")
            if self.action.action_type == ActionType.Move:
                self.agent_from = location
                new_agent_row = location[0] + action.agent_dir.d_row
                new_agent_col = location[1] + action.agent_dir.d_col
                self.agent_to = (new_agent_row, new_agent_col)
                self.required_free = self.agent_to
                self.will_become_free = self.agent_from
                self.box_from = None
                self.box_to = None
            elif self.action.action_type == ActionType.NoOp:
                self.box_from = None
                self.box_to = None
                self.agent_from = location
                self.agent_to = location
                self.required_free = None
                self.will_become_free = None
            else:
                raise NotImplementedError("Auto create only implemented for Move/NoOp Actions")

        else:
            
            #tuples
            self.box_from = None
            self.box_to = None
            self.agent_from = None
            self.agent_to = None
            self.required_free = None
            self.will_become_free = None
        



    def __eq__(self, other):
        return self.agent_id == other.agent_id and self.action == other.action

    #har en action --> UnfoldedAction
    def get_UnfoldedAction( agent: 'Agent', action: 'Action'):
        new_agent_row = agent.row + action.agent_dir.d_row
        new_agent_col = agent.col + action.agent_dir.d_col
        unfolded_action = UnfoldedAction(action, agent.id_)
        unfolded_action.agent_from = (agent.row, agent.col)
        log('agent from: ' + str(unfolded_action.agent_from))
        unfolded_action.agent_to = (new_agent_row, new_agent_col)
        log('agent to: ' + str(unfolded_action.agent_to))
        unfolded_action.will_become_free = (agent.row, agent.col)
        unfolded_action.required_free = (new_agent_row, new_agent_col)
        return unfolded_action

