import time
import csv



class Profiler:
    level: str
    running_functions: list
    agent: str
    start_time: time

    def __init__(self, level, agent, output):
        self.output = output
        self.level = level
        self.agent = agent
        self.running_functions = []

    def start(self, function_name):
        self.start_time = time.time()
        self.running_functions.append(function_name)

        writer = csv.writer(self.output)
        writer.writerow([self.level, self.agent, function_name, "START", 0, round(self.start_time, 4)])


    
    def stop(self):
        function_name = self.running_functions.pop()
        writer = csv.writer(self.output)
        writer.writerow([self.level, self.agent, function_name, "END",round(time.time() - self.start_time, 4), round(self.start_time, 4)])



