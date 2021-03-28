from experta import *
import spacy
from spacy.matcher import Matcher, PhraseMatcher
from .scraper import scrape
from .DB import connect_db

MultiTokenDictionary = {
    "game_info" : [
        [{"POS": "PRON"}, {"POS": "AUX"}, {"POS": "DET"}, {"POS":"NOUN"}, {"POS": "ADP"}], # "What is the game about"
        [{"POS": "ADP"}, {"POS": "DET", "OP": "*"}, {"POS": "NOUN"}], # "About the game"
        [{"LEMMA": {"IN": ["information", "info", "about"]}}]
    ],

    "play_instructions" : [
        [{"POS": "ADV"}, {"POS": "ADP"}, {"POS": "VERB"}], # "How to play"
        [{"POS": "ADV"}, {"POS": "PART"}, {"POS": "VERB"}], # "How to play"
        [{"LEMMA": "instruction"}],
    ],
    
    "reviews" : [
        [{"LEMMA": "review"}],
        [{"POS" : "PRON"}, {"POS" : "VERB", "LEMMA": {"IN": ["review"]}}],
        
    ],

    "help": [
        [{"LEMMA": "help"}],

    ]

                
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
        self.games_list = connect_db()


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

    def update_message_chain(self, message, priority = "high", response_required = True):
        """
        priority == high - first message
        priority == low - at the end of the stack.
        """
        if (len(self.message) == 1 and
                self.default_message in self.message and
                priority != 7):
            self.message = []
        if priority == "low":
            self.message.append({'message' : message, 'response_required' : response_required})
        elif priority == "high":
            self.message.insert(0, {'message' : message, 'response_required' : response_required})
        elif priority == 7:
            self.tags += message

    def get_single_match(self, doc, pattern):
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
        print("_initial_aciton facts:", self.facts)
        if len(self.message) == 0:
            self.message = [self.default_message]
        for key, value in self.knowledge.items():
            this_fact = {key: value}
            yield Fact(**this_fact)
        if "action" not in self.knowledge.keys():
            yield Fact(action="game_selection")
        if "end" not in self.knowledge.keys():
            yield Fact(end=False)
        yield Fact(extra_info_req=False)


    @Rule(AS.f1 << Fact(action="game_selection"),
        Fact(message_text=MATCH.message_text),
        salience=100)
    def game_selection(self, f1, message_text):
        print("game_selection", message_text)
        print("Facts available.", self.facts)
        doc = self.process_nlp(message_text)
        matches = self.get_multiple_matches(doc, MultiTokenDictionary['help'])
        game_in_db = None
        first_message = True
        
        # User written 'help'
        if len(matches) > 0:
            print("HELP")
            first_message = False
            self.update_message_chain("Here is a list of games I can help with.", response_required=False)
            ############## Add here all games available ###############
            self.update_message_chain("Which game are you interested in?", priority="low")
            self.modify(f1, action="help")
            self.halt()
        else:
            # user typed a particular game name
            for game, rating in self.games_list:
# print("Comparison: ", game.lower(), message_text)
                if game.lower() == message_text.lower():
                    print("Game within Database")
                    game_in_db = True
                    break
                else:
                    print("Can't find the game asked for. :(")
                    if not first_message:
                        game_in_db = False
                    
        print("Game found?", game_in_db)
        # self.modify(f1, action="random")
        if game_in_db == True:
            message = "Selected game: {}".format(message_text)
            self.update_message_chain(message, response_required=False, priority="high")
            self.modify(f1, action="game_selected")
        elif game_in_db == False:
            message = "Sorry, currently I don't support {}. For a list of supported games, type 'help'.".format(message_text).capitalize()
            self.update_message_chain(message)
            self.modify(f1, action="game_not_found")

    @Rule(AS.f1 << Fact(action="help"),
        salience=95)
    def help_requested(self, f1):
        self.update_message_chain("Here is a list of games I can help with.", response_required=False)
        self.update_message_chain("Which game are you interested in?", priority="low")
        self.modify(f1, action="game_selection")


    @Rule(AS.f1 << Fact(action="game_selected"),
        salience=95)
    def game_selected(self, f1):
        print("game selected facts", self.facts)
        self.update_message_chain("I can help with X Y |", priority="low")
        self.modify(f1, action="random")
    
    @Rule(Fact(action="game_not_found"),
        salience=96)
    def game_not_found(self):
        print("game not found facts", self.facts)
        self.update_message_chain("Fact:Game not found. Awwww, I'll cry ;( ")

    @Rule(AS.f1 << Fact(action="random"),
          Fact(message_text=MATCH.message_text),
          salience=99)
    def direct_action(self, f1, message_text):
        """

        """
        print("FACTS:", self.knowledge)
        doc = self.process_nlp(message_text)
        # print out what the tokens are in the user input
        # for token in doc:
        #     print(token.text, token.pos_, token.dep_, token.lemma_)
        print("message from user", message_text)
        
        matches = self.get_multiple_matches(doc, MultiTokenDictionary['game_info'])
        if len(matches) > 0:
            print("GAME INFO")
            self.update_message_chain("Game_info: Ok, let's get you informed!", response_required=False, priority="high")
            # self.progress = "dl_dt_al_rt_rs_na_nc_"
            self.declare(Fact(general_information = True))
            self.modify(f1, action="information")
        else:
            matches = self.get_multiple_matches(doc, MultiTokenDictionary['play_instructions'])
            if (len(matches) > 0) :
                print("Instructions")
                self.update_message_chain("Instructions: Cool, here's how to play Chess!", response_required=False, priority="high")
                self.update_message_chain("You move X to Y and then Z goes AAAAAA!", priority = "low")
                print(self.message)
                self.declare(Fact(instructions = True))
                self.modify(f1, action="instructions")
            else:
                matches = self.get_multiple_matches(doc, MultiTokenDictionary['reviews'])
                if (len(matches) > 0) :
                    print("Reviews")
                    self.update_message_chain("Reviews: This game has some nice reviews. Check this out:", response_required=False, priority="high")
                    self.update_message_chain("<strong>Very nice game!</strong>", response_required=False, priority="low")
                    self.modify(f1, action="reviews")
                    self.declare(Fact(reviews = True))
                # 
                # if (len(matches) > 0) :
                #     self.update_message_chain("(M)Reviews: This game has some nice reviews. Check this out:", response_required="Random")
                #     self.update_message_chain("<strong>Very nice game!</strong>", priority=0)
                # else:
                #     print("AH HELL NAW!")
        
    @Rule(Fact(action="information"),
         salience= 91)
    def provide_general_info(self):
        game_content = scrape("Chess")
        # self.update_message_chain("What information do you need? I can provide general information")
        self.update_message_chain("General information about {}.".format(game_content['name']), response_required=False, priority="low")
        self.update_message_chain(game_content['description'], response_required=False, priority="low")
        self.update_message_chain("Would you like to know anything else?", priority="low")
        # self.declare(Fact(more_info_needed = True))


    @Rule(Fact(action="instructions"),
        Fact(instructions = True),
         salience= 99)
    def provide_instructions(self):
        self.update_message_chain("After you move the Z, you experience equilibrium!", priority="high", response_required=False)
        self.update_message_chain("Instructions: Would you like to know anything else?", priority="low")

    @Rule(Fact(action="reviews"),
        Fact(reviews = True),
         salience= 99)
    def provide_reviews(self):
        game_content = scrape("Chess")
        self.update_message_chain("Reviews about {}.".format(game_content['name']), response_required=False, priority="high")
        self.update_message_chain("Thing is there are no reviews :(", response_required=False, priority="low")

    @Rule(Fact(more_info_needed = True),
         salience= 90)
    def get_more_info(self):
        self.update_message_chain("Ah.... What now...?", priority="high")
    