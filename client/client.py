import sys
from enum import Enum

# #domain
# hospital
# #levelname
# Example1
# #colors
# blue: 0, A, B
# red: 1, C
# #initial
# ++++++++
# +      +
# + ++B+ +
# ++++B+ +
# ++++B+ +
# ++++B+ +
# ++++B+ +
# ++++B+ +
# ++++B+ +
# ++++B+ +
# ++++B+ ++
# +++1AC 0+
# +++++++++
# #goal
# ++++++++
# +      +
# + ++ + +
# ++++ + +
# ++++ + +
# ++++ + +
# ++++ + +
# ++++ + +
# ++++ + +
# ++++ + +
# ++++ +C++
# +++   A +
# +++++++++
# #end


class Section(Enum):
    DOMAIN = 1
    LEVELNAME = 2
    COLORS = 3
    INITIAL = 4
    GOAL = 5
    END = 6


class Client:
    def __init__(self, server_messages):
        print("tes", file=sys.stderr, flush=True)
        print("vAIkings client", file=sys.stdout, flush=True)

        line = server_messages.readline().rstrip()

        section = None

        while line:
            if(line == "#end"):
                section = Section.END
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
                if(section == Section.END):
                    print((section.name, line), file=sys.stderr, flush=True)
                    continue
                elif(section == Section.DOMAIN):
                    print((section.name, line), file=sys.stderr, flush=True)
                elif(section == Section.LEVELNAME):
                    print((section.name, line), file=sys.stderr, flush=True)
                elif(section == Section.COLORS):
                    print((section.name, line), file=sys.stderr, flush=True)
                elif(section == Section.INITIAL):
                    print((section.name, line), file=sys.stderr, flush=True)
                elif(section == Section.GOAL):
                    print((section.name, line), file=sys.stderr, flush=True)

            line = server_messages.readline().rstrip()



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
