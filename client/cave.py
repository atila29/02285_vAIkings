
class Cave:

    id_: int
    locations: list
    goals: list
    entrance: (int, int)
    dead_end: (int, int)
    occupied: bool

    def __init__(self, id_, dead_end):
        self.dead_end = dead_end
        self.occupied = False
        self.id_ = id_
        self.locations = [dead_end]
        self.goals = []
    
    def is_next_goal(self, goal, state):
        for g in self.goals:
            if g == goal:
                return True
            if not state.is_goal_satisfied(g):
                return False

