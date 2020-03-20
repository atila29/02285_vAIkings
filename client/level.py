from typing import List, Dict

class LevelElement(object):
    pass

class Wall(LevelElement):
    pass

class Space(LevelElement):
    pass

class Goal(LevelElement):
    name = None

    def __init__(self, name, row, col):
        self.name = name
        self.row = row
        self.col = col

#Class containing the static level information
class Level:
    #List containing "empty level",  i.e. walls, free space, goals
    level = List[List[LevelElement]]
    #Dictionary containing goals corresponding to different letters
    goals = Dict[str, List[Goal]]

    def __init__(self):
        self.level = [] 
        self.goals = {} 

    def add_goal(self, char, row, col):
        goal = Goal(char, row, col)
        self.level[row].append(goal)
        #Add goal to goal list
        if(char in self.goals):
            self.goals[char].append(goal)
        else:
            self.goals[char] = [goal]