import sys
from enum import Enum
import re

from box import Box
from state import State, LEVEL
from level import LevelElement, Wall, Space, Goal, Level, AgentElement
from agent import Agent, BDIAgent
from action import Action, ActionType, Dir

class Section(Enum):
    DOMAIN = 1
    LEVELNAME = 2
    COLORS = 3
    INITIAL = 4
    GOAL = 5


class Client:
    
    initial_state: 'State'
    agents = []
    agent_dic = {}
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
        #End while

        #Initialise the BDI Agents
        
        for agent_pos in self.initial_state.agents:
            agent = self.initial_state.agents[agent_pos]
            self.agents.append(BDIAgent(agent.name, agent.color, agent.row, agent.col, self.initial_state))
            self.agent_dic[agent.name] = self.agents[-1]

    def search(self, initial_state):
        current_state = initial_state
        while True:
            plans = []
            #Loop through agents
            for agent_id in sorted(self.agent_dic.keys()):
                #Get plan from each
                plans.append(self.agent_dic[agent_id].get_next_action(current_state))
            joint_actions = self.create_joint_actions(plans)
            
            #Check if conflicts in joint plan, Loop until we resolve all conflicts
            conflicts = self.check_for_conflicts(joint_actions)
            if conflicts:    
                #If yes : Replan ?? (Naive: make some use NoOp)
                self.solve_conflicts(joint_actions, conflicts)
            
            #Otherwise: Execute
            current_state = self.execute_joint_actions(joint_actions, current_state)

            #If we reached goal
            if self.check_goal_status(current_state):
                break

    """
        Takes a list of unfolded actions as input (assumed to be applicable when viewed as single actions)
        i.e. Each of the individual actions has its precondition satisfied in the current state
        
        OUTPUT: Returns a list of list of indexes of conflicting actions
        Each list in the list will contain the index of the agents that conflict with eachother 
        e.g. if [i,j] is in the list it means:
        "The ith action on the list conflicts with the jth action on the list"
    """    
    def check_for_conflicts(self, joint_actions) -> '[[Tuple, Tuple, ...], ...]':
        
        #print("joint actions" + str(joint_actions), file=sys.stderr, flush=True)
        conflicts = []
        #Case a in TA: Two actions attempt to move two distinct objects into the same cell.
        all_agent_to = [action.agent_to for action in joint_actions]
        all_box_to = [action.box_to for action in joint_actions]
        combined_list = all_agent_to + all_box_to
        duplicates = set([tuple(x) for x in combined_list if combined_list.count(x) > 1])
        for dupe in duplicates:
            if dupe != tuple([]):
                conflicts.append([i for i in range(len(all_box_to)) if tuple(all_agent_to[i]) == dupe or tuple(all_box_to[i]) == dupe]) #<-- Currently possible saves longer lists than tuples
        #Case b in TA: Two actions attempt to move the same box 
        all_box_from = [action.box_from for action in joint_actions]

        duplicates = set([tuple(x) for x in all_box_from if all_box_from.count(x) > 1])

        for dupe in duplicates:
            if dupe != tuple([]):
                conflicts.append([i for i in range(len(all_box_from)) if tuple(all_box_from[i]) == dupe]) #<-- Currently possible saves longer lists than tuples
        return conflicts #<-- Currently may contain duplicates since agents might conflict in both cases


        
    def create_joint_actions(self, list_of_plans) -> '[UnfoldedAction, ...]':
        #If a plan is just one unfolded action:
        return [plan for plan in list_of_plans]

    """
        Returns True if all goals have a box with the right letter on it.
        Otherwise it returns False
    """
    def check_goal_status(self, current_state) -> 'Bool':
        for goal_pos in LEVEL.goals_by_pos:
            if goal_pos not in current_state.boxes:
                return False
            if current_state.boxes[goal_pos].name != LEVEL.goals_by_pos[goal_pos].name:
                return False
        return True

    
    
    def execute_joint_actions(self,joint_actions, current_state) -> 'State':
        #Send to server and get response
            # TODO
        #Update State: Move agents and boxes, 
        new_state = State(current_state)

        msg = repr(joint_actions[0].action)
        if len(joint_actions) > 1:
            for action in joint_actions[1:]:
                msg = msg + ';' + repr(action.action) 
        
        print(msg, file=sys.stderr, flush=True)

        print(msg, flush = True)
        result = sys.stdin.readline().rstrip()
        print(result, file=sys.stderr, flush=True)
        result = result.split(';')
        if "false" in result:
            print("Something went wrong. Client send invalid move", file=sys.stderr, flush=True)
            print("agents at: ", file=sys.stderr, flush=True)
            for agent in self.agents:
                print((agent.id, agent.row, agent.col), file=sys.stderr, flush=True)
            all_agent_to = [action.agent_to for action in joint_actions]
            all_box_to = [action.box_to for action in joint_actions]
            combined_list = all_agent_to + all_box_to
            print("combined_list:" + str(combined_list), file=sys.stderr, flush=True)
            duplicates = set([tuple(x) for x in combined_list if combined_list.count(x) > 1])
            print("duplicates:" + str(duplicates), file=sys.stderr, flush=True)
            print("Check for conflicts:" + str(self.check_for_conflicts(joint_actions)), file=sys.stderr, flush=True)
            raise RuntimeError
        
        # TODO: Make sure to pop the action from the agents plan (either directly or through a execute function) 
        # Remark: Don't pop if action is NoOP from conflict resolves
        for action in joint_actions:
            if action.action.action_type == ActionType.NoOp:
                continue
            #update box location in state
            if action.box_from != []:
                box = new_state.boxes.pop(tuple(action.box_from))
                new_state.boxes[tuple(action.box_to)] = Box(box.name, box.color, *action.box_to)
            #update agent location in state
            agent = new_state.agents.pop(tuple(action.agent_from))
            new_state.agents[tuple(action.agent_to)] = AgentElement(agent.name, agent.color, *action.agent_to)
            #update agents with their new location
            bdi_agent = self.agent_dic[action.agent_id]
            bdi_agent.row, bdi_agent.col = action.agent_to
        return new_state

    def solve_conflicts(self, joint_actions, conflicts) -> '[UnfoldedAction, ...]':
        for conflict in conflicts:
            for index in conflict[1:]:
                joint_actions[index].action = Action(ActionType.NoOp, Dir.N, Dir.N)


def main():
    # Read server messages from stdin.
    server_messages = sys.stdin

    # Use stderr to print to console through server.
    print('SearchClient initializing. I am sending this using the error output stream.',
          file=sys.stderr, flush=True)

    client = Client(server_messages)
    
    client.search(client.initial_state)

    #Print result summary (time, memory, solution length, ... )


if __name__ == '__main__':

    # Run client.
    main()
