from bot.RE import ReasoningEngine
from experta import *


class Chat():

    def __init__(self):
        self.chat_engine = ReasoningEngine()
        print()

    def add_message(self, author, message_text):
        if author != "bot":
            self.chat_engine.reset()
            self.chat_engine.declare(Fact(message_text=message_text))
            self.chat_engine.run()
            message = self.chat_engine.message.pop(0)
            tags = self.chat_engine.tags
            self.chat_engine.tags = ""
            return [message['message'],
                    message['response_required']]

    def pop_message(self):
        if len(self.chat_engine.message) > 0:
            message = self.chat_engine.message.pop(0)
        else:
            message = { 'message' : "Chat: Sorry! Something has gone wrong with this chat. "
                           "Please reload the page",
                        'response_required' : True }
        tags = self.chat_engine.tags
        self.chat_engine.tags = ""
        return message