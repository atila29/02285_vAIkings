from logger import log

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

    def update_status(self, state):
        for location in self.locations:
            if location in state.agents:
                if not self.occupied:
                    log("Agent {} entered Cave {} so it is now occupied".format(state.agents[location].id_,self.id_), "CAVES", False)
                self.occupied = True
                return
        if self.occupied:
            log("The last agent left cave {}. So it is now empty".format(self.id_), "CAVES", False)
        self.occupied = False

    # region String representations
    def __repr__(self):
        return "Cave {}".format(self.id_)

    def __str__(self):
        return self.__repr__()
    # endregion

