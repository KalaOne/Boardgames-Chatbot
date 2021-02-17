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
            print(message)
            tags = self.chat_engine.tags
            self.chat_engine.tags = ""

            return message