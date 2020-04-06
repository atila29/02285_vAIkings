from typing import List, Dict

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

class Box:

    color: str # maybe enums?
    letter: str
    row = -1
    col = -1

    def __init__(self, letter, color, row, col):
        self.color = color
        self.letter = letter
        self.row = row
        self.col = col

    def __repr__(self):
        return self.color + " Box with letter " + self.letter
        

    def __str__(self):
        return self.letter

   

#Class containing the static level information
class Level:
    #List containing "empty level",  i.e. walls, free space, goals
    level = List[List[LevelElement]]
    #Dictionary containing goals corresponding to different letters
    goals = Dict[str, List[Goal]]
    goals_by_pos = {}

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