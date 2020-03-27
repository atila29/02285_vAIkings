from action import Action



class Precondition:
    pass

class Effect:
    pass

# box_movement = [box_from, box_to]
# agent_movement = [agent_from, agent_to]
# free = [required_free, will_become_free]

class ActionSchema(object):
    precondition: Precondition
    action: Action
    effect: Effect

    # def __init__(self, precondition, action, effect):
    def __init__(self, action, effect):
        # self.precondition = precondition
        self.action = action
        self.effect = effect

    

