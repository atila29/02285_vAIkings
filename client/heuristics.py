from level import Goal, Space
import copy
from action import Dir
import time
from util import log
from state import LEVEL

class SimpleHeuristic:

    def __init__(self, agent_id, location):
        self.agent_id = agent_id
        if isinstance(location, Goal):
            self.location = (location.row, location.col)
        else:
            self.location = location

    def h(self, state):
        
        #Find agent position in this state
        for agent in state.agents.values(): 
            if agent.id_ == self.agent_id:
                agent_row = agent.row
                agent_col = agent.col

        return abs(agent_row-self.location[0]) + abs(agent_col - self.location[1])

    def f(self, state):
        return self.h(state)

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

class Heuristic2:
    #save a copy of the level for each goal, key: goal pos, Values: two dimensional list with distance to goal in empty level in each position
    distances = {}
    directions = [Dir.N, Dir.S, Dir.E, Dir.W]
    
    def __init__(self):
        self.analyse_level()

    #pair = (box, location)
    def h(self, state, pair, agent):
        intended_box, location = pair
        box_id = intended_box.id_
        
        if isinstance(location, Goal):
            location= (location.row, location.col) 

        #Find agent position in this state
        for a in state.agents.values(): 
            if a.id_ == agent.id_:
                agent_row = a.row
                agent_col = a.col

        #Find box position in this state
        for box in state.boxes.values(): #box = state.boxes[intended_box.id]
            if box.id_ == box_id:
                box_row = box.row
                box_col = box.col
        
        #distance to box
        d1 = abs(agent_row - box_row) + abs(agent_col - box_col)
        #distance from box to goal
        d2 = self.distances[location][box_row][box_col]

        #TODO: generalise in case location is not a goal
        return max(d1 + d2, self.distances[location][agent_row][agent_col])

    def f(self, state, pair, agent):
        return self.h(state, pair, agent) #what about the g-values?

    """
        Analyse the level and get the distances to the goals in an "empty" level
    """
    def analyse_level(self):
        log("Starting to analyze level for the heuristic function", "Analysis", False)
        time_start = time.time()
        for location in LEVEL.goals_by_pos:
            #for each goal generate a level
            self.distances[location] = copy.deepcopy(LEVEL.level)
            current_map = self.distances[location]
            
            #current goal location
            row,col = location
            current_map[row][col] = 0
            
            #list of locations that needs to be updated
            frontier = [location]
            
            #keep updating until no more reachable spaces
            while True:
                #no more to explore
                if len(frontier) == 0:
                    break   
                
                #new location to update/expand
                new_location = frontier.pop(0)
                neighbours = self.update_neighbours(new_location, current_map)
                frontier = frontier + neighbours

            #Mark unreachable spaces with infinity
            for row in range(len(current_map)):
                for col in range(len(current_map[row])):
                    if isinstance(current_map[row][col], Space) or isinstance(current_map[row][col], Goal):
                        current_map[row][col] = float("inf")
            
            #For DEBUG:
            self.print_map(location)
                        
        #Done?
        log("Ended analysis after {} seconds".format(time.time()-time_start), "Analysis", False)


    #return list of neighbours that now have a better cost
    def update_neighbours(self, location,current_map):
        result = []
        row, col = location
        cost = current_map[row][col]
        for direction in self.directions:
            neighbour = current_map[row+direction.d_row][col + direction.d_col]
            if isinstance(neighbour, int):
                if neighbour > cost + 1:
                    result.append((row+direction.d_row,col + direction.d_col))
                    current_map[row+direction.d_row][col + direction.d_col] = cost + 1
            else:
                if isinstance(neighbour, Space) or isinstance(neighbour, Goal):
                    current_map[row+direction.d_row][col + direction.d_col] = cost + 1
                    result.append((row+direction.d_row,col + direction.d_col))
        return result

    def print_map(self, location):
        log("Printing distances to goal with letter {} at location {}:".format(LEVEL.goals_by_pos[location], location), "MAP", False)
        current_map = self.distances[location]
        lines =[]
        for row in current_map:
            line  =[]
            for elm in row:
                line.append(str(elm))
            lines.append(''.join(line))
        log("\n".join(lines), "MAP", False)




 