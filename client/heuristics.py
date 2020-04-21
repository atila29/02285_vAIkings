from level import Goal

class Heuristic:
    
    def __init__(self, agent: 'BDIAgent'):
        self.agent = agent

    #could add an if-statement of whether the agent is next to the box or not
    def h(self, state, pair = None) -> 'in#find position of agent':
        
        if pair is None:
            intended_box, goal = self.agent.intentions
        else:
            intended_box, goal = pair

        #Find agent position in this state
        for agent in state.agents.values(): 
            if agent.id_ == self.agent.id_:
                agent_row = agent.row
                agent_col = agent.col

        #Find box position in this state
        for box in state.boxes.values(): #box = state.boxes[intended_box.id]
            if box.id_ == intended_box.id_:
                box_row = box.row
                box_col = box.col
        
        # distance from agent to box to goal
        if isinstance(goal, Goal):
            dist_box_goal = abs(goal.row - box_row) + abs(goal.col - box_col) # dist from box to goal
        else:
            dist_box_goal = abs(goal[0] - box_row) + abs(goal[1] - box_col)
        dist_agt_box = abs(agent_row - box_row) + abs(agent_col - box_col) # dist from agent to box
        dist = dist_box_goal + dist_agt_box # total dist
        return dist

    def f(self, state, pair=None): #greedy
        return self.h(state, pair)




 