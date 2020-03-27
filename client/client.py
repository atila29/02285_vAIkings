import sys
from enum import Enum
import re

from box import Box
from state import State, LEVEL
from level import LevelElement, Wall, Space, Goal, Level, AgentElement
from agent import Agent

class Section(Enum):
    DOMAIN = 1
    LEVELNAME = 2
    COLORS = 3
    INITIAL = 4
    GOAL = 5


class Client:
    
    initial_state: 'State'
    agents = []
    current_conflicts = []
    
    def __init__(self, server_messages):
        print("vAIkings client", file=sys.stdout, flush=True) # publish our client's name to the server

        line = server_messages.readline().rstrip()

        section = None

        item_dict = {}
        self.initial_state = State()
        
        row = 0

        
        while line:
            if(line == "#end"):
                break
            elif(line == "#domain"):
                section = Section.DOMAIN
            elif(line == "#levelname"):
                section = Section.LEVELNAME
            elif(line == "#colors"):
                section = Section.COLORS
            elif(line == "#initial"):
                section = Section.INITIAL
            elif(line == "#goal"):
                section = Section.GOAL
                row = 0
            else:
                if(section == Section.DOMAIN):
                    print((section.name, line), file=sys.stderr, flush=True)
                elif(section == Section.LEVELNAME):
                    print((section.name, line), file=sys.stderr, flush=True)
                elif(section == Section.COLORS):
                    print((section.name, line), file=sys.stderr, flush=True)

                    color = line.split(":")[0]
                    items = line.split(":")[1].replace(" ", "").split(",")

                    for item in items:
                        item_dict[item] = color
                    
                elif(section == Section.INITIAL):
                    print((section.name, line), file=sys.stderr, flush=True)
                    LEVEL.level.append([])

                    for col, char in enumerate(line):
                        # print((row, col, char), file=sys.stderr, flush=True)
                        if(char == '+'):
                            LEVEL.level[row].append(Wall())
                        elif(char==' '):
                            LEVEL.level[row].append(Space())
                        elif(re.match(r"\d", char)): # match digits, Agents
                            LEVEL.level[row].append(Space()) # can add agent instead?
                            self.initial_state.agents[(row,col)] = AgentElement(char, item_dict[char], row, col)
                            self.agents.append(BDIAgent(char, item_dict[char], row, col, None, None))
                        elif(re.match(r"[A-Z]", char)): # match capital letters, Boxes
                            LEVEL.level[row].append(Space())
                            self.initial_state.boxes[(row,col)] = Box(char, item_dict[char], row, col)
                    row += 1
                elif(section == Section.GOAL):
                    print((section.name, line), file=sys.stderr, flush=True)
                    for col, char in enumerate(line):
                        # print((row, col, char), file=sys.stderr, flush=True)
                        if(re.match(r"[A-Z]", char)):
                            LEVEL.add_goal(char, row, col)

                    row += 1


            line = server_messages.readline().rstrip()
        # print(LEVEL, file=sys.stderr, flush=True)
        # print(initial_state, file=sys.stderr, flush=True)
        self.initial_state.print_current_state()
        for pos in self.initial_state.agents:
            test_agent_element = self.initial_state.agents[pos]
            test_agent = Agent(test_agent_element.row, test_agent_element.col, test_agent_element.color, test_agent_element.name)
            children = test_agent.get_children(self.initial_state)
            print("Agent " + str(pos), file=sys.stderr, flush=True)
            if(len(children) != 0):
                children[0].print_current_state()

    def search(self, initial_state):
        current_state = initial_state
        while True:
            plans = []
            #Loop through agents
            for agent in self.agents:
                #Get plan from each
                plans.append(agent.extract_plan(current_state))
            joint_actions = self.create_joint_actions(plans)
            
            #Check if conflicts in joint plan, Loop until we resolve all conflicts
            while self.check_for_conflicts(joint_actions):    
                #If yes : Replan ?? (Naive: make some use NoOp)
                joint_actions = self.solve_a_conflict(joint_actions)
            #Otherwise: Execute
            current_state = self.execute_joint_actions(joint_actions, current_state)

            #If we reached goal
            if self.check_goal_status(current_state):
                break

        
    def check_for_conflicts(self, joint_actions) -> 'Bool':
        raise NotImplementedError

    def create_joint_actions(self, list_of_plans) -> '[Action, ...]':
        raise NotImplementedError

    def check_goal_status(self, current_state) -> 'Bool':
        raise NotImplementedError

    def execute_joint_actions(self,joint_actions, current_state) -> 'State':
        #Send to server and get response
        #Update State
        #Update all agents so they know they've moved (i.e. make all agents excute)   
        raise NotImplementedError

    def solve_a_conflict(self, joint_actions) -> '[Action, ...]':
        raise NotImplementedError


def main():
    # Read server messages from stdin.
    server_messages = sys.stdin

    # Use stderr to print to console through server.
    print('SearchClient initializing. I am sending this using the error output stream.',
          file=sys.stderr, flush=True)

    client = Client(server_messages)

    #Client.doit()
    #Print result summary (time, memory, solution length, ... )


if __name__ == '__main__':

    # Run client.
    main()
