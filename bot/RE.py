from experta import *
import spacy
from spacy.matcher import Matcher, PhraseMatcher
from .scraper import scrape


SingleTokenDictionary = {
    "game_info": [{"LEMMA": {"IN": ["information", "info"]}}],
    "num_players": [{"LEMMA": "player"}],
    "play_instructions" : [ {"LEMMA": "instruction"}],
    "general_information" : [{"LEMMA" : "about"}],
    "reviews" : [{"LEMMA": "review"}],

 }

MultiTokenDictionary = {
    "play_instructions" : [
        [{"LEMMA": "instruction"}],
        [{"POS": "ADV"}, {"POS": "ADP"}, {"POS": "VERB"}] # Example "How to play"
        
    ],
    "general_information" : [
        [{"POS": "PRON"}, {"POS": "AUX", "OP": "*"}, # Example "What is the game about"
        {"POS": "NOUN", "LEMMA" : {"IN" : ["game", "boardgame"]}}, 
        {"POS": "ADP"} ],
        [{"LEMMA" : "about"}],
    ],
    "reviews" : [
        [{"POS" : "PRON"}, {"POS" : "VERB", "LEMMA": [{"IN": "review"}]}],
        [{"LEMMA": "review"}]
    ],

                
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
        self.default_message = {'message': "Default: I'm sorry. I don't know how to help with that just yet. Please try again",
                                'response_required': True}
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

    def update_message_chain(self, message, priority = 1, response_required = True):
        """
        priority == 1 - at the back of the stack
        priority == 0 - first message.
        """
        if (len(self.message) == 1 and
                self.default_message in self.message and
                priority != 7):
            self.message = []
        if priority == 0:
            self.message.append({'message' : message, 'response_required' : response_required})
        elif priority == 1:
            self.message.insert(0, {'message' : message, 'response_required' : response_required})
        elif priority == 7:
            self.tags += message

    def get_single_match(self, doc, pattern):
        for token in doc:
            print(token.text, token.pos_, token.dep_, token.lemma_)
        matcher = Matcher(self.nlp.vocab)
        if "newMatch" in matcher:
            matcher.remove("newMatch")
        matcher.add("newMatch", None, pattern)
        matches = matcher(doc)

        try:
            if len(matches) > 0:
                for match_id, start, end in matches:
                    return doc[start:end]
        except Exception as e:
            print(e)
            return e
        return ""

    def get_multiple_matches(self, doc, pattern):
        match = None
        for p in pattern:
            matches = self.get_single_match(doc, p)
            if matches:
                break
        return matches

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
        matches = self.get_single_match(doc, SingleTokenDictionary['game_info'])

        if len(matches) > 0:
            self.update_message_chain("Ok, let's get you informed!", response_required=False)
            # self.progress = "dl_dt_al_rt_rs_na_nc_"
            self.modify(f1, action="general")

        else:
            # matches = self.get_multiple_matches(doc, MultiTokenDictionary['play_instructions'])
            matches = self.get_single_match(doc, SingleTokenDictionary['play_instructions'])
            if (len(matches) > 0) :
                self.update_message_chain("Cool, here's how to play Chess!", response_required=False)
                self.update_message_chain("You move X to Y and then Z goes AAAAAA!", priority = 0)

    # @Rule(Fact(action="general"),
    #      salience= 99)
    # def provide_general_info(self):
        