

class Heuristic():
    def __init__(self, initial_state: 'State'):
        pass


    def h(self, state: 'State') -> 'int':
        boxes = []
        goals = []
        for row in range(state.MAX_ROW):
            for col in range(state.MAX_COL):
                if state.box_at(row, col):
                    boxes.append((row, col))
                if state.goal_at(row, col):
                    goals.append((row, col))
        dist = []
        for goal in goals:
            for box in boxes:
                # manhattan distance from goal(0,1) til box (0,1)
                dist_box_goal = abs(goal[0] - box[0]) + abs(goal[1] - box[1])
                # manhattan distance from agent location til box
                dist_box_agent = abs(state.agent_row - box[0]) + abs(state.agent_col - box[1])
                # adding total distance
                dist.append(dist_box_goal + dist_box_agent)
        return min(dist)  # return minimal distance

    def f(self): #greedy
        return self.h()




