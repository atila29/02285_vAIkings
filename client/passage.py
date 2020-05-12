from logger import log

class Passage:

    id_: int
    locations: list
    goals: list
    fst_entrance: (int, int)
    snd_entrance: (int, int)
    occupied: bool
    entrances: list

    def __init__(self, id_):
        self.occupied = False
        self.id_ = id_

        self.locations = []
        self.goals = []
        self.entrances = []
    
    def is_next_goal(self, goal, state):
        for g in self.goals:
            if g == goal:
                return True
            if not state.is_goal_satisfied(g):
                return False

    def update_status(self, state):
        locations = self.locations + self.entrances
        for location in locations:
            if location in state.agents:
                if not self.occupied:
                    log("Agent {} entered passage {}. So it is now occupied".format(state.agents[location].id_, self.id_), "PASSAGES", False)
                self.occupied = True
                return
        if self.occupied:
            log("The last agent left passage {}. So it is now empty".format(self.id_), "PASSAGES", False)
        self.occupied = False

    # region String representations
    def __repr__(self):
        return "Passage {}".format(self.id_)

    def __str__(self):
        return self.__repr__()
    # endregion

