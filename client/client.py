import sys
from enum import Enum
import re

from agent import Agent
from box import Box
from state import State
from level_element import LevelElement, Wall, Space

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
            else:
                if(section == Section.DOMAIN):
                    print((section.name, line), file=sys.stderr, flush=True)
                elif(section == Section.LEVELNAME):
                    print((section.name, line), file=sys.stderr, flush=True)
                elif(section == Section.COLORS):
                    print((section.name, line), file=sys.stderr, flush=True)

                    color = line.split(":")[0]
                    items = line.split(":")[1].strip().split(",")

                    for item in items:
                        item_dict[item] = color
                elif(section == Section.INITIAL):
                    print((section.name, line), file=sys.stderr, flush=True)
                    initial_state.level.append([])

                    for col, char in enumerate(line):
                        print((row, col, char), file=sys.stderr, flush=True)
                        if(char == '+'):
                            initial_state.level[row].append(Wall())
                    row += 1
                elif(section == Section.GOAL):
                    print((section.name, line), file=sys.stderr, flush=True)

            line = server_messages.readline().rstrip()
        print(initial_state.level, file=sys.stderr, flush=True)




def main():
    # Read server messages from stdin.
    server_messages = sys.stdin

    # Use stderr to print to console through server.
    print('SearchClient initializing. I am sending this using the error output stream.',
          file=sys.stderr, flush=True)

    client = Client(server_messages)


if __name__ == '__main__':

    # Run client.
    main()
