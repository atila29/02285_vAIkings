from typing import List, Dict
from cave import Cave
from action import Dir
from util import log

class LevelElement:
    pass

class Wall(LevelElement):
    def __str__(self):
        return "+"

class Space(LevelElement):
    def __str__(self):
        return " "

class Goal(LevelElement):
    letter = None
    

    def __init__(self, letter, row, col):
        self.letter = letter
        self.row = row
        self.col = col
        self.cave = None

    def __str__(self):
        return str.lower(self.letter)

 
class AgentElement:

    color: str # maybe enums?
    id_: str
    row = -1
    col = -1

    def __init__(self, id_: str, color: str, row: int, col: int):
        self.color = color
        self.id_ = id_
        self.row = row
        self.col = col

    def __repr__(self):
        return self.color +" Agent with letter " + self.id_

    def __str__(self):
        return self.id_
        
    def __eq__(self, other):
        return self.id_ == other.id_

class Box:

    color: str # maybe enums?
    letter: str
    id_: str
    row = -1
    col = -1

    def __init__(self, id_, letter, color, row, col):
        self.id_ = id_
        self.color = color
        self.letter = letter
        self.row = row
        self.col = col


    def __repr__(self):
        return self.color + " Box with letter " + self.letter
        

    def __str__(self):
        return self.letter

    def __eq__(self, other):
        return other is not None and self.id_ == other.id_

   

#Class containing the static level information
class Level:
    #List containing "empty level",  i.e. walls, free space, goals
    level = List[List[LevelElement]]
    #Dictionary containing goals corresponding to different letters
    goals = Dict[str, List[Goal]]
    goals_by_pos = {}
    caves = {} #key is entrance location 

    def __init__(self):
        self.level = [] 
        self.goals = {} 

    def add_goal(self, char, row, col):
        goal = Goal(char, row, col)
        self.level[row][col] = goal
        #Add goal to goal list 1
        if(char in self.goals):
            self.goals[char].append(goal)
        else:
            self.goals[char] = [goal]
        #Add goal to goal list 2
        self.goals_by_pos[(row,col)] = goal

    def pre_process(self):
        log("Starting preprocessing of caves", "CAVES", False)
        # loop through level and find deadends (3 walls around one spot)
        deadends = self.find_deadends()

        log("Found the following dead ends {}".format(deadends), "CAVES", False)

        # For each deadend, create the corresponding 'cave'
        for i in range(len(deadends)):
            self.create_cave(deadends[i], i)
        

        # If multiple goals are in the same cave -> force priority on them
        #   Goal closest to dead end first, "lock" the rest
        # 
        # Optional: Find tunnels (1-wide passages with two exits)
        #   If more than three goals in one tunnel -> force priority
        #  

    """
        Output: list of locations for deadends
    """
    def find_deadends(self):
        result = []
        for row in range(len(self.level)):
            for col in range(len(self.level[row])):
                if isinstance(self.level[row][col], Space) or isinstance(self.level[row][col], Goal):
                    #count number of walls around
                    count = self.count_walls_around((row,col))
                    if count ==3:
                        log("Element {} at location {} identified as a dead end".format(self.level[row][col], (row,col)), "CAVES", False)
                        result.append((row,col))
        return result

    def count_walls_around(self, location):
        row, col = location
        count = 0
        for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
            if isinstance(self.level[row+direction.d_row][col + direction.d_col], Wall):
                count = count + 1
        return count

    def create_cave(self, location, id_):
        cave = Cave(id_ = id_, dead_end = location)

        loc = location

        #explore cave:
        while True:           
            #Check if location is a goal
            if loc in self.goals_by_pos:
                goal = self.goals_by_pos[loc]
                cave.goals.append(goal)
                goal.cave = cave

            #find next space
            row,col = loc
            for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
                if isinstance(self.level[row+direction.d_row][col + direction.d_col], Wall):
                    continue
                loc = (row+direction.d_row, col + direction.d_col) 
            
            #check if still in cave
            count = self.count_walls_around(loc)
            if count < 2:
                cave.entrance = cave.locations[-1]
                break
            cave.locations.append(loc)
            
        self.caves[cave.entrance] = cave
        log("Created the {}th cave. Entrance: {}, goals: {}, locations: {}".format(id_, cave.entrance, cave.goals, cave.locations), "CAVES", False)







                