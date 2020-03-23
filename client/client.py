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
    def __init__(self, server_messages):
        print("vAIkings client", file=sys.stdout, flush=True) # publish our client's name to the server

        line = server_messages.readline().rstrip()

        section = None

        item_dict = {}

        initial_state = State()
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
                            initial_state.agents[(row,col)] = AgentElement(char, item_dict[char], row, col)
                        elif(re.match(r"[A-Z]", char)): # match capital letters, Boxes
                            LEVEL.level[row].append(Space())
                            initial_state.boxes[(row,col)] = Box(char, item_dict[char], row, col)
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
        initial_state.print_current_state()
        for pos in initial_state.agents:
            test_agent_element = initial_state.agents[pos]
            test_agent = Agent(test_agent_element.row, test_agent_element.col, test_agent_element.color, test_agent_element.name)
            children = test_agent.get_children(initial_state)
            print("Agent " + str(pos), file=sys.stderr, flush=True)
            if(len(children) != 0):
                children[0].print_current_state()



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
