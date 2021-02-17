from experta import *
import spacy
from spacy.matcher import Matcher


TokenDictionary = {
    "game_info": [{"LEMMA": {"IN": ["information", "info"]}}],
    "num_players": [{"LEMMA": {"IN": ["player"]}}],

 }

class ReasoningEngine(KnowledgeEngine):

    def __init__(self):
        super().__init__()
        # Spacy 
        self.nlp = spacy.load("en_core_web_sm")

        # Knowledge dictionary
        self.knowledge = {}
        self.progress = ""

        # UI output
        self.default_message = "I'm sorry. I don't know how to help with that just yet. Please try again"
        self.message = []
        self.tags = ""


    def process_nlp(self, text_to_process):
        """
        Sends user input to be proceed by spacy.
        """
        return self.nlp(text_to_process)


    def declare(self, *facts):
        """
        Overrides super class' method declare to add the facts to the knowledge
        dictionary (self.knowledge)
        """
        new_fact = super().declare(*facts)
        if new_fact:
            for g, val in new_fact.items():
                if g not in ["__factid__", "message_text", "extra_info_req",
                             "extra_info_requested"]:
                    self.knowledge[g] = val
        return new_fact

    def update_message_chain(self, message, priority = 1):
        """
        priority == 0 - at the back of the stack
        priority == 1 - first message.
        """
        if priority == 0:
            self.message.append(message)
        elif priority == 1:
            self.message.insert(0, message)
        elif priority == 7:
            self.tags += message

    @DefFacts()
    def _initial_action(self):
        if len(self.message) == 0:
            self.message = [self.default_message]
        for key, value in self.knowledge.items():
            this_fact = {key: value}
            yield Fact(**this_fact)
        if "action" not in self.knowledge.keys():
            yield Fact(action="chat")
        if "end" not in self.knowledge.keys():
            yield Fact(end=False)
        yield Fact(extra_info_req=False)


    @Rule(AS.f1 << Fact(action="chat"),
          Fact(message_text=MATCH.message_text),
          salience=100)
    def direct_action(self, f1, message_text):
        """
        Directs the engine to the correct action for the message text passed

        Parameters
        ----------
        f1: Fact
            The Fact containing the current action
        message_text: str
            The message text passed by the user to the Chat class
        """
        doc = self.process_nlp(message_text)
        print("spacy doc", doc)
        matcher = Matcher(self.nlp.vocab)
        matcher.add("game_info", None, TokenDictionary['game_info'])
        print("matcher", matcher)
        matches = matcher(doc)
        if len(matches) > 0:
            # likely to be a booking
            self.update_message_chain("Ok, let's get you informed.")
            self.progress = "dl_dt_al_rt_rs_na_nc_"
            self.modify(f1, action="general")
        # else:
        #     matcher.add("DELAY_PATTERN", None, TokenDictionary['delay'])
        #     matches = matcher(doc)
        #     if len(matches) > 0:
        #         # likely to be a delay prediction
        #         self.update_message_chain("Using the latest train data, I can "
        #                                   "predict how long you'll be delayed."
        #                                   " <br><i>Only available from Norwich to "
        #                                   "London Liverpool Street and "
        #                                   "intermediate stations.</i>",
        #                                   req_response=False)
        #         self.progress = "dl_al_dt_dd_"
        #         self.modify(f1, action="delay")
        