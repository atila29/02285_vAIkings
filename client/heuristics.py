
class Heuristic():
    
    def __init__(self, agent:'BDIAgent'):
        self.agent = agent
        pass

    def h(self) -> 'int':
        # distance from agent to box to goal
        box, goal = self.agent.intentions
        dist_box_goal = abs(goal.row - box.row) + abs(goal.col - box.col) # dist from box to goal
        dist_agt_box = abs(self.agent.row - box.row) + abs(self.agent.col - box.col) # dist from agent to box
        dist = dist_box_goal + dist_agt_box # total dist
        return dist

    def f(self): #greedy
        return self.h()




