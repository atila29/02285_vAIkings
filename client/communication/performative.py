# Inquiries and announcements:
#     1.query-if.  “Is boxBat locationL?” -> might not be necessary because all knowledge is currently available?
#     2.inform.  “BoxBis at locationL.”
# Requests:
#     3.request.  “Please move BoxBto locationL.”
#     4.agree.  “OK, I’ll do it.”
#     5.refuse.  “I won’t do it.”
#     6.failure.  “I didn’t manage to do it.”
# Proposals:
#     6.cfp.  Call for proposal.  “Send me your proposals for moving boxBtolocationLwithin timeT.”
#     7.propose.  “I can do it by ...”
#     8.accept-proposal.  “OK, I accept your proposal.”
#     9.reject-proposal.  “No, that’s not good enough.”

# class RequestMoveBoxTo:
#     def __init__(self, location):
#         self.location = location

# class RequestMoveSpecificBoxTo:
#     def __init__(self, boxId, location):
#         self.boxId = boxId
#         self.location = location

class CfpMoveBoxTo:
    def __init__(self, location, cost = None):
        self.location = location

class CfpMoveSpecificBoxTo:
    def __init__(self, box, location, cost = None):
        self.box = box
        self.location = location



