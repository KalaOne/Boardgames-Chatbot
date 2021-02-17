from bot.RE import ReasoningEngine
from experta import *


class Chat():

    def __init__(self):
        self.chat_engine = ReasoningEngine()

    def add_message(self, author, message_text):

        if author != "bot":
            self.chat_engine.reset()
            self.chat_engine.declare(Fact(message_text=message_text))
            self.chat_engine.run()
            message = self.chat_engine.message.pop(0)
            print("IN CHAT ",message)
            tags = self.chat_engine.tags
            self.chat_engine.tags = ""

            return message

    def pop_message(self):
        if len(self.chat_engine.message) > 0:
            message = self.chat_engine.message.pop(0)
        else:
            message = { 'message' : "Sorry! Something has gone wrong with this chat. "
                           "Please reload the page" }
        return message