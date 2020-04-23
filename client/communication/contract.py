class Contract:

    def __init__(self, manager, contractor, performative, cost, start):
        self.manager = manager
        self.contractor = contractor
        self.performative = performative
        self.cost = cost
        self.start = start

    # region String representations
    def __repr__(self):
        return str(self.performative)

    def __str__(self):
        return self.__repr__()
    # endregion