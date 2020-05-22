import uuid

class Request:
    id: uuid.UUID

    def __init__(self,agent_id, area, move_boxes = True, request_id = None, ignore_locations = []):
        self.agent_id = agent_id
        self.move_boxes = move_boxes
        self.area = area
        self.id_ = request_id
        self.ignore_locations = ignore_locations
        self.boxes_in_the_area = []
        self.agents_in_the_area = []
        self.agents_that_have_checked_request_already = []
        self.goal = None
        self.box = None
        if request_id is None:
            self.id_ = uuid.uuid4()
        else:
            self.id_ = request_id


    # region String representations
    def __repr__(self):
        if self.move_boxes:
            return "Request(Agent: {}, id: {}): Move boxes and agents from area: {}. \n Agents that have checked: {} ".format(self.agent_id, self.id_, self.area ,self.agents_that_have_checked_request_already)
        return "Request(Agent: {}, id: {}): Move agents from area: {} ".format(self.agent_id, self.id_, self.area)

    def __str__(self):
        return self.__repr__()
    # endregion
    
    def __eq__(self, other):
        return self.id_ == other.id_

    

