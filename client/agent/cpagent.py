from agent.bdiagent import BDIAgent
from state import LEVEL
from communication.performative import CfpMoveSpecificBoxTo
from communication.blackboard import BLACKBOARD
from communication.contract import Contract
from communication.request import Request
from logger import log
from cave import Cave
from passage import Passage
from action import Action, ActionType, Dir

class CPAgent(BDIAgent):

    # TODO: refactor function
    def find_wanted_passages_and_cave(self):
        
        wanted_passages = []
        wanted_cave = []

        next_action = self.current_plan[0]
        if self.will_move_block_passage_entrance(next_action):
            
            row, col = next_action.required_free
            
            explored_entrances=[(row,col)]
            passages_to_explore = [(p, (row,col)) for p in LEVEL.map_of_passages[row][col]]
            

            while len(passages_to_explore) > 0:
                log("passages_to_explore: {}".format(passages_to_explore), "TEST", False)
                passage, enter = passages_to_explore.pop()
                #Do I want to enter one of them? -> add to list
                if self.passage_on_path(passage):
                    wanted_passages.append((passage, enter))
                    for entrance in passage.entrances:
                        if entrance in explored_entrances:
                            continue
                        new_passages = [(p,entrance) for p in LEVEL.map_of_passages[entrance[0]][entrance[1]] if p != passage]
                        explored_entrances.append(entrance)
                        passages_to_explore = passages_to_explore + new_passages

        if len(wanted_passages) > 0:
            last_passage, enter = wanted_passages[-1]
            for entrance in last_passage.entrances:
                if entrance == enter:
                    continue
                exit_location = entrance
        else:
            exit_location = next_action.required_free
        caves_to_explore= LEVEL.map_of_caves[exit_location[0]][exit_location[1]]
        if caves_to_explore is not None:
            for cave in caves_to_explore:
                if self.cave_on_path(cave):
                    wanted_cave.append((cave, exit_location))

        if len(wanted_cave) == 0 and len(wanted_passages) > 0:
            #check if the wanted goal is in the last passage
            last_passage, entrance = wanted_passages[-1]
            location = None
            
            #get goal location
            if isinstance(self.intentions, Contract):
                if isinstance(self.intentions.performative, CfpMoveSpecificBoxTo):
                    box = self.intentions.performative.box
                    location = self.intentions.performative.location
                else:
                    raise NotImplementedError("Unrecognized performative")    
            if self.intentions is not None and not isinstance(self.intentions, Request):
                box, goal = self.intentions
                location = (goal.row, goal.col)
            
            #Check if goal in passage
            if location is not None and location in last_passage.locations:
                #create artificial cave
                artificial_cave = Cave(None, location)
                artificial_cave.entrance = entrance
                end = entrance
                for pos in last_passage.locations:
                    if pos == location:
                        break
                    if self.is_adjacent(pos, end):
                        end = pos
                        artificial_cave.locations.insert(1, end)
                        if pos in LEVEL.goals_by_pos:
                            artificial_cave.goals.append(LEVEL.goals_by_pos[pos])    
                artificial_cave.update_status(self.beliefs)
                wanted_cave = [artificial_cave, entrance]
                wanted_passages = wanted_passages[:-1]

        return wanted_passages, wanted_cave
        
    def passage_on_path(self, passage):
        for action in self.current_plan:
            if action.required_free in passage.locations:
                return True
        return False

    def cave_on_path(self, cave):
        for action in self.current_plan:
            if action.required_free == cave.locations[-1]:
                return True
        return False

    def is_adjacent(self, pos1, pos2):
        for dir in [Dir.N, Dir.S, Dir.E, Dir.W]:
            if pos1[0] + dir.d_row == pos2[0] and pos1[1] + dir.d_col == pos2[1]:
                return True
        return False

    def box_is_needed(self, box):       
        #count boxes with box.color and box.letter
        box_count = 0
        for b in self.beliefs.boxes.values():
            if b.letter == box.letter and b.color == box.letter:
                box_count += 1
        
        #count goals with letter
        goal_count = len(LEVEL.goals[box.letter])

        if box_count <= goal_count:
            return True
        return False

    def box_is_claimed_by_me(self, box):
        return box.id_ in BLACKBOARD.claimed_boxes and BLACKBOARD.claimed_boxes[box.id_] == self.id_


    def box_is_claimed_by_other(self, box):
        return box.id_ in BLACKBOARD.claimed_boxes and BLACKBOARD.claimed_boxes[box.id_] != self.id_


    def will_move_block_passage_entrance(self, next_action = None):
        if next_action is None:
            next_action = self.current_plan[0]
        if next_action.action.action_type == ActionType.NoOp:
            # row, col = next_action.agent_from
            # return LEVEL.map_of_passages[row][col] is not None
            return False
        location = next_action.required_free
        passages_at_location = LEVEL.map_of_passages[location[0]][location[1]]
        if passages_at_location is None:
            return False
        for passage in passages_at_location:
            if location in passage.entrances:
                return True
        return False

    def will_move_block_cave_entrance(self, next_action=None):
        if next_action is None:
            next_action = self.current_plan[0]
        if next_action.action.action_type == ActionType.NoOp:
            #TODO
            return False
        location = next_action.required_free
        caves_at_location = LEVEL.map_of_caves[location[0]][location[1]]
        if caves_at_location is None:
            return False
        for cave in caves_at_location:
            if cave.entrance == location:
                return True 
        return False

            #TODO: If we call this when trying to do a request we will probably not be allowed to enter, since the cave/passage will be blocked by the box we wanna move. How do we handle this?
    def is_free(self, cave_or_passage):
        if isinstance(cave_or_passage, Cave):
            cave = cave_or_passage
 
            for agent_id, c in BLACKBOARD.claimed_caves.items():
                if cave in c and agent_id != self.id_:
                    log("Cave {} is not free since it is claimed by another agent".format(cave), "IS_FREE", False)
                    return False
            

            #Start at the end of the cave and look for boxes and goals
            #Cave is marked as not free if:
                # 1: An unsatisfied goal is blocked (behind a box inside the cave, irrelevant if on a goal or not) 
                # 2: A needed box (claimed, or count to see if any spares) is blocked (behind another box inside the cave, irrelevant if on a goal or not )
            end = None

            for i in range(len(cave.locations)):
                temp = cave.locations[i]

                #If on goal, skip if satisfied, otherwise stop:
                if temp in LEVEL.goals_by_pos:
                    if not self.beliefs.is_goal_satisfied(LEVEL.goals_by_pos[temp]):
                        break
                    else:
                        end = i

                #check for box
                elif temp in self.beliefs.boxes:
                    box = self.beliefs.boxes[temp]
                    #These are not allowed to be blocked, so stop
                    if self.box_is_claimed_by_me(box):
                        end = i
                        break
                    elif self.box_is_needed(box) or self.box_is_claimed_by_other(box):
                        end = i - 1 #TODO: CHECK INDEX? 
                        break

            #clear whole cave
            if end is None:
                area_required = [cave.entrance] + cave.locations
            #clear until end
            else:
                area_required = [cave.entrance] + cave.locations[end+1:]
            
            for location in area_required:
                if location in self.beliefs.boxes:
                    if self.beliefs.boxes[location].id_ not in BLACKBOARD.claimed_boxes or BLACKBOARD.claimed_boxes[self.beliefs.boxes[location].id_] != self.id_:
                        box= self.beliefs.boxes[location]
                        log("Cave {} is not free since there is a box in the required area. {} Box with letter {} at: {}, required area: {}".format(cave, box.color, box.letter, location, area_required), "IS_FREE", False)
                        return False
            if cave.occupied:
                if (self.row, self.col) in cave.locations + [cave.entrance]:
                    log("Cave {} is occupied by the agent itself".format(cave), "IS_FREE", False)
                    return True
                else:
                    log("Cave {} (area: {}) is not free since it is occupied by another agent".format(cave_or_passage, cave_or_passage.locations), "IS_FREE", False)
                    return False

        if isinstance(cave_or_passage, Passage):
            for agent_id in BLACKBOARD.claimed_passages:
                if agent_id != self.id_ and cave_or_passage in BLACKBOARD.claimed_passages[agent_id]:
                    log("Passage {} (area: {}) is claimed by another agent (id: {})".format(cave_or_passage, cave_or_passage.locations, agent_id), "IS_FREE", False)
                    return False
            for location in cave_or_passage.locations:
                if location in self.beliefs.boxes:
                    box = self.beliefs.boxes[location]
                    if not self.box_is_claimed_by_me(box):
                        log("Passage {} (area: {}) is blocked by a box. (box: {})".format(cave_or_passage, cave_or_passage.locations, box), "IS_FREE", False)
                        return False
        
            if cave_or_passage.occupied:
                if (self.row, self.col) in cave_or_passage.locations + cave_or_passage.entrances:
                    log("Passage {} is occupied by the agent itself".format(cave_or_passage), "IS_FREE", False)
                    return True
                log("Passage {} (area: {}) is not free since it is occupied by another agent".format(cave_or_passage, cave_or_passage.locations), "IS_FREE", False)
                return False
            
        log("Cave/passage {} is free".format(cave_or_passage), "IS_FREE", False)
        return True

    def make_request(self, cave_or_passage):

        if isinstance(cave_or_passage, Cave):
            cave = cave_or_passage
            end = None
            for i in range(len(cave.locations)):
                temp = cave.locations[i]
                if temp in LEVEL.goals_by_pos:
                    if not self.beliefs.is_goal_satisfied(LEVEL.goals_by_pos[temp]):
                        break
                    else:
                        end = i
            #clear whole cave
            if end is None:
                area_required = [cave.entrance] + cave.locations
            #clear until end
            else:
                area_required = [cave.entrance] + cave.locations[end+1:]
            
            request = Request(self.id_, area_required)
            BLACKBOARD.add_request(request, self.id_)

        if isinstance(cave_or_passage, Passage):
            request = Request(self.id_, cave_or_passage.locations + cave_or_passage.entrances)
            BLACKBOARD.add_request(request, self.id_)

    """
        OUTPUT: True if next part of path is clear (connected passages + cave)
                False otherwise
    """
    def clear_path_through_passages_and_cave(self):
        
        wanted_passages, wanted_cave = self.find_wanted_passages_and_cave()
        log("wanted_passages: {}, wanted_cave: {}".format(wanted_passages, wanted_cave), "TEST", False)

        can_move = True
        for elm, entrance in wanted_passages + wanted_cave:
            if not self.is_free(elm):
                can_move = False
                break
        
        if can_move:
            for elm, entrance in wanted_passages + wanted_cave:
                BLACKBOARD.claim(self.id_, elm)
                #TODO: remove claims somewhere!
            return True
        
        #TODO: Maybe the agent should consider taking another route instead of waiting
        for elm, entrance in wanted_passages + wanted_cave:
            self.make_request(elm)
        
        return False

    def left_claimed_area(self):
        next_action = self.current_plan[0]
        if next_action.required_free is None or next_action.will_become_free is None:
            return (False, None)
        
        #entrance becomes free
            #was in claimed area

        free = next_action.will_become_free
        old_location = next_action.agent_from
        if LEVEL.map_of_caves[free[0]][free[1]] is not None:
            for cave in LEVEL.map_of_caves[free[0]][free[1]]:
                if free == cave.entrance and old_location in cave.locations + [cave.entrance]:
                    if self.id_ in BLACKBOARD.claimed_caves and cave in BLACKBOARD.claimed_caves[self.id_]:
                        return (True, cave)
        if LEVEL.map_of_passages[free[0]][free[1]] is not None:
            for pas in LEVEL.map_of_passages[free[0]][free[1]]:
                if free in pas.entrances and old_location in pas.locations + pas.entrances:
                    if self.id_ in BLACKBOARD.claimed_passages and pas in BLACKBOARD.claimed_passages[self.id_]:
                        return (True, pas)

        # if next_action.action.action_type == ActionType.Move:
        #     if next_action.agent_from in [cave.entrance for cave in LEVEL.caves.values()]:
        #         for cave in 
        # row, col = next_action.will_become_free
        # location = next_action.required_free
        # if LEVEL.map_of_caves[row][col] is not None:
        #     for cave in LEVEL.map_of_caves[row][col]:
        #         if (row,col) in cave.locations+[cave.entrance]:
        #             if location not in cave.locations:
        #                 return (True, cave)
        # if LEVEL.map_of_passages[row][col] is not None:
        #     for pas in LEVEL.map_of_passages[row][col]:
        #         if (row,col) in pas.locations + pas.entrances:
        #             if location not in pas.locations:
        #                 return (True, pas)
        return (False, None)
        #new_action.will_become_free in passage/cave locations and new_action.required_free not in location + entrance

    """
        Check the claimed passages and caves. 
        Returns true if they are still free to go through
        Returns False otherwise
    """
    def claims_are_sound(self):
        log("Testing sound claims", "TEST", False)
        #test all claimed passages
        if self.id_ in BLACKBOARD.claimed_passages:
            for passage in BLACKBOARD.claimed_passages[self.id_]:
                if not self.is_free(passage):
                    log("passage {} not free".format(passage), "TEST", False)
                    return False
        
        if self.id_ in BLACKBOARD.claimed_caves:
            for cave in BLACKBOARD.claimed_caves[self.id_]:
                if not self.is_free(cave):
                    log("cave {} not free".format(cave), "TEST", False)
                    return False
        return True


    def have_claims(self):
        log("Testing if agent have claims. result: {}".format(self.id_ in BLACKBOARD.claimed_passages or self.id_ in BLACKBOARD.claimed_caves), "CLAIMS", False)
        return self.id_ in BLACKBOARD.claimed_passages or self.id_ in BLACKBOARD.claimed_caves
    