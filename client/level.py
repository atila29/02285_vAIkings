import sys

from typing import List, Dict
from cave import Cave
from action import Dir
from logger import log
from util import reverse_direction
from passage import Passage
from action import Dir

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
        self.passage = None

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
    caves = {} # key is id
    passages = {} #key is id
    map_of_passages: list
    map_of_caves: list

    wall_count = []

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

    def pre_process(self, state):
        log("Starting preprocessing of caves", "CAVES", False)
        
        self.count_all_walls()

        # loop through level and find deadends (3 walls around one spot)
        deadends = self.find_deadends()

        log("Found the following dead ends {}".format(deadends), "CAVES", False)

        # For each deadend, create the corresponding 'cave'
        for i in range(len(deadends)):
            self.create_cave(deadends[i], i)
        
        #update occupation status on caves
        for cave in self.caves.values():
            cave.update_status(state)
        self.map_caves()

        self.find_passages()
        self.map_passages()
        # If multiple goals are in the same cave -> force priority on them
        #   Goal closest to dead end first, "lock" the rest
        # 
        # Optional: Find tunnels (1-wide passages with two exits)
        #   If more than three goals in one tunnel -> force priority
        #  

    def count_all_walls(self):
        self.wall_count = []
        for row in range(len(self.level)):
            self.wall_count.append([])
            for col in range(len(self.level[row])):
                if isinstance(self.level[row][col], Wall):
                    self.wall_count[row].append(None)
                if isinstance(self.level[row][col], Space) or isinstance(self.level[row][col], Goal):
                    self.wall_count[row].append(self.count_walls_around((row, col)))
            

    """
        Output: list of locations for deadends
    """
    def find_deadends(self):
        result = []
        for row in range(len(self.level)):
            for col in range(len(self.level[row])):
                if isinstance(self.level[row][col], Space) or isinstance(self.level[row][col], Goal):
                    #count number of walls around
                    #count = self.count_walls_around((row,col))
                    if self.wall_count[row][col] ==3:
                        result.append((row,col))
        return result

    def count_walls_around(self, location):
        row, col = location
        count = 0
        for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
            new_row = row+direction.d_row
            new_col = col + direction.d_col
            if new_row in range(len(self.level)) and new_col in range(len(self.level[row])) and isinstance(self.level[new_row][new_col], Wall):
                count = count + 1
        return count

    def create_cave(self, location, id_):
        cave = Cave(id_ = id_, dead_end = location)

        loc = location

        #explore cave:
        log("Starting to explore the {}th cave".format(id_), "CAVES", False)  
        while True:         
            #Check if location is a goal
            if loc in self.goals_by_pos:
                goal = self.goals_by_pos[loc]
                cave.goals.append(goal)
                goal.cave = cave

            #find next space
            row,col = loc
            loc = None
            for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
                if isinstance(self.level[row+direction.d_row][col + direction.d_col], Wall):
                    continue
                loc = (row+direction.d_row, col + direction.d_col)
                if loc in cave.locations:
                    loc = None
                    continue
                else:
                    break
            
            #Cave has no entrance
            if loc is None:
                log("found no new locations. Cave has no entrance. Removing from list", "CAVES", False)

                # cave.entrance = None
                # self.caves[location] = cave
                # log("Created the {}th cave. Entrance: {}, goals: {}, locations: {}".format(id_, cave.entrance, cave.goals, cave.locations), "CAVES", False)
                return
            
            #check if still in cave
            count = self.count_walls_around(loc)
            if count < 2:
                log("Found {} walls around location {}. So cave {} is fully explored".format(count, loc, id_), "CAVES", False)
                cave.entrance = loc
                break

            cave.locations.append(loc)
            
        self.caves[cave.id_] = cave
        log("Created the {}th cave. Entrance: {}, goals: {}, locations: {}".format(id_, cave.entrance, cave.goals, cave.locations), "CAVES", False)


    def find_passages(self):
        passages = []
        for row in range(len(self.level)):
            passages.append([])
            for col in range(len(self.level[row])):
                if isinstance(self.level[row][col], Wall):
                    passages[row].append(False)
                if isinstance(self.level[row][col], Space) or isinstance(self.level[row][col], Goal):
                    if self.wall_count[row][col] == 2:
                        # #TODO: Corner test
                        # if not self.is_corner((row, col)):
                        #     passages[row].append(True)
                        # else:
                        #     passages[row].append(False)
                        passages[row].append(not(self.is_corner((row,col))))
                    else:
                        passages[row].append(False)

        #remove caves
        for cave in self.caves.values():
            for location in cave.locations:
                row, col = location
                passages[row][col] = False 

        count = 0
        while True:
            
            #pick location and start exploring passage
            location = None
            for row in range(len(self.level)):
                for col in range(len(self.level[row])):   
                    if passages[row][col]:
                        location = (row,col)
                        break
                if location is not None:
                    break
            if location is None:
                break
            
            #explore passage
            self.create_passage(location, count, passages)
            #self.print_passage_map(passages)
            count = count+1

    def create_passage(self, location, id_, passages):
        passage = Passage(id_ = id_)

        #explore
        log("Starting to explore the {}th passage".format(id_), "PASSAGES", False)  
        temp = [location]
        passage.locations.append(location)
        passages[location[0]][location[1]] = False
        
        while temp:
            loc = temp.pop()
            #Check if location is a goal
            if loc in self.goals_by_pos:
                goal = self.goals_by_pos[loc]
                passage.goals.append(goal)
                goal.passage = passage
        
            #find next spaces()
            row, col = loc
            for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
                if isinstance(self.level[row+direction.d_row][col + direction.d_col], Wall):
                    continue
                loc = (row+direction.d_row, col + direction.d_col)
                if loc in passage.locations:
                    continue
                else:
                    #check if part of passage or entrance
                    if passages[loc[0]][loc[1]]: 
                        passage.locations.append(loc)
                        temp.append(loc)
                        passages[loc[0]][loc[1]] = False
                    else:
                        log("Found entrance for passage {} at location {}".format(id_, loc), "PASSAGES", False)
                        passage.entrances.append(loc)
        
        log("Done creating passage {}. Locations: {}. Entrances: {}".format(id_, passage.locations, passage.entrances), "PASSAGES", False)
        self.passages[id_] = passage
        
    def map_passages(self):

        #Create empty map
        self.map_of_passages = []
        for row in range(len(self.level)):
            self.map_of_passages.append([])
            for col in range(len(self.level[row])):
                self.map_of_passages[row].append(None)

        for passage in self.passages.values():
            locations = passage.locations + passage.entrances
            for row, col in locations:
                if self.map_of_passages[row][col] is None:
                    self.map_of_passages[row][col] = []
                self.map_of_passages[row][col].append(passage)

    def map_caves(self):
        #Create empty map
        self.map_of_caves = []
        for row in range(len(self.level)):
            self.map_of_caves.append([])
            for col in range(len(self.level[row])):
                self.map_of_caves[row].append(None)

        for cave in self.caves.values():
            locations = cave.locations + [cave.entrance]
            for row, col in locations:
                if self.map_of_caves[row][col] is None:
                    self.map_of_caves[row][col] = []
                self.map_of_caves[row][col].append(cave)


    def print_passage_map(self, passages):
        lines =[]
        for row in passages:
            line  =[]
            for elm in row:
                line.append(str(elm))
            lines.append(''.join(line))
        print("\n".join(lines), file=sys.stderr, flush=True)

    def is_corner(self, location):
        log("Testing if {} is a corner".format(location), "PASSAGES", False)
        row,col = location
        wall_directions = []
        for direction in [Dir.N, Dir.S, Dir.E, Dir.W]:
            if isinstance(self.level[row + direction.d_row][col + direction.d_col], Wall):
                wall_directions.append(direction)
        if wall_directions[0] == reverse_direction(wall_directions[1]):
            log("Walls are opposite, so not a corner", "PASSAGES", False)
            return False
        test_row, test_col = row, col
        for direction in wall_directions:
            test_row = test_row - direction.d_row
            test_col = test_col - direction.d_col
        if not isinstance(self.level[test_row][test_col], Wall):
            log("location {} is identified as an open corner".format(location), "PASSAGES", False)
            return True
        else:
            return False

                