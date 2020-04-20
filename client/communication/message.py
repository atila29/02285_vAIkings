import sys
import uuid

class Message:
    
    def __init__(self, senderId, performative, conversationId = None, receiver = None):
        self.performative = performative
        self.id_ = uuid.uuid4()
        self.senderId = senderId
        
        if conversationId is None:
            conversationId = uuid.uuid4()
        self.conversationId = conversationId

        if receiver is not None:
            self.receiver = receiver

