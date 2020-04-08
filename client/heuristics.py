
class Heuristic:
    
    def __init__(self, agent: 'BDIAgent'):
        self.agent = agent

    #could add an if-statement of whether the agent is next to the box or not
    def h(self, state) -> 'in#find position of agent':
        
        intended_box, goal = self.agent.intentions

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
        dist_box_goal = abs(goal.row - box_row) + abs(goal.col - box_col) # dist from box to goal
        dist_agt_box = abs(agent_row - box_row) + abs(agent_col - box_col) # dist from agent to box
        dist = dist_box_goal + dist_agt_box # total dist
        return dist

    def f(self, state): #greedy
        return self.h(state)




 