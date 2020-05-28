import sys
import csv
import copy
import re

with open(sys.argv[1], 'r') as f:
    with open('summary.csv', 'w', newline='\n') as file:
        writer = csv.writer(file)

        writer.writerow(["lvl_name", "lvl_solved","actions_used", "last_action_time (in seconds)"])

        lines = f.readlines()
        for line in lines:
            if(re.match("Level name: ", line)):
                lvl_name = line.replace("Level name: ", "").replace("\n", "")
            elif(re.match("Level solved: ", line)):
                lvl_solved = line.replace("Level solved: ", "").replace("\n", "")
            elif(re.match("Actions used: ", line)):
                actions_used = line.replace("Actions used: ", "").replace("\n", "")
            elif(re.match("Last action time: ", line)):
                last_action_time = line.replace("Last action time: ", "").replace("\n", "").replace(" seconds.", "")
            else:
                writer.writerow([lvl_name, lvl_solved,actions_used, last_action_time])

