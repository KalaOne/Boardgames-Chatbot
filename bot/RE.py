from experta import *
import spacy
from spacy.matcher import Matcher, PhraseMatcher
from .scraper import scrape
from .DB import connect_db, get_specific_game_from_db
import difflib



MultiTokenDictionary = {
    "yes": [
        [{"LOWER": {"IN": ["yes", "yeah"]}}],
        [{"LOWER": {"IN": ["y", "yep", "yeh", "ye"]}}]
        ],
    "no": [
        [{"LOWER": {"IN": ["no", "n"]}}],
        [{"LOWER": {"IN": ["nope", "nah", "na"]}}]
        ],

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
        [{"LEMMA": "assistance"}]

    ],

    "suggest_game" : [
        [{"POS": "VERB", "LEMMA" : "suggest"}], # suggest
        [{"POS": "VERB", "LEMMA" : "suggest"}, 
        {"POS": "DET", "OP":"*"}, 
        {"POS": "NOUN", "LEMMA" : "game"}], # suggest (a) game

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
        self.game_data = None
        self.boardgame = ""
        #genre ,max_players, play_time, rating,
        self.game_suggestion_journey = "gn_pl_pt_rt_"
        self.ans_g = self.ans_p = self.ans_t = self.ans_r = False
        self.ask1 = False


    def game_name_similarity(self, game_name):
        result = None
        # for game in self.games_list:
        #     seq = difflib.SequenceMatcher(lambda x: x in " \t", game_name, game)
        #     r = seq.ratio()*100
        #     if r > 70:
        #         result = game
        
        return result

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
            yield Fact(action="path_choice")
        if "end" not in self.knowledge.keys():
            yield Fact(end=False)
        yield Fact(extra_info_req=False)


    @Rule(AS.f1 << Fact(action="path_choice"),
        Fact(message_text=MATCH.message_text),
        salience=100)
    def game_selection(self, f1, message_text):
        print("path_choice", message_text)
        print("Facts available.", self.facts)
        doc = self.process_nlp(message_text)
        matches = self.get_multiple_matches(doc, MultiTokenDictionary['help'])
        game_in_db = None
        first_message = True

        # for token in doc:
        #     print(token.text, token.pos_, token.dep_, token.lemma_)


        # User written 'help'
        if len(matches) > 0:
            first_message = False
            self.update_message_chain("I have access to over 200,000 games. I can help you get specific information about a particular game or \
                suggest a game based on your requirements.", response_required=False)
            self.update_message_chain("What do you want me to do?", priority="low")
            self.modify(f1, action="help")
            # self.halt()
        else:
            # user wants game suggestion
            matches = self.get_multiple_matches(doc, MultiTokenDictionary['suggest_game'])
            if len(matches) > 0:
                self.update_message_chain("Suggest_game: Okay, I need some details so I know what to suggest.", priority="high", response_required=False)
                self.declare(Fact(suggest_game = True))
                self.modify(f1, action="suggest_game")
            else:
                # user has written specific game name
                game, closest_match = get_specific_game_from_db(message_text)
                print("GAME SELECTED ", game)
                print("Closest game ", closest_match)
                if game:
                    # the specified game is in DB
                    message = "Selected game: {}.".format(game[0][1])
                    self.boardgame = game[0][1]
                    self.update_message_chain(message, response_required=False, priority="high")
                    self.modify(f1, action="game_selected")
                else: 
                    # Game is not in DB. Suggest alternative
                    req_yes_no = "{REQ:" + "Choice}"
                    if not self.ask1:
                        message = "Sorry, it seems that '{}' doesn't exist in the database. \
                            The closest game I found is '{}'.  {}Do you want to continue with the suggested game?".format(message_text.capitalize(), closest_match[0].capitalize(), req_yes_no)
                        self.update_message_chain(message, priority="high")
                        self.ask1 = True
                    choice = self.check_yes_no(message_text)
                    if choice:
                        if choice.text == 'yes':
                            self.boardgame = game[0][1]
                            self.modify(f1, action="game_selected")
                        elif choice.text == 'no':
                            self.update_message_chain("Okay. Then please re-type the game you're interested in.", priority="high")
                        else:
                            msg = "{}Please write 'yes' or 'no'. "
                            self.update_message_chain(msg.format(req_yes_no), priority="low")
                            self.modify(f1, action="path_choice")
                        

                    
                    
        print("Game found?", game_in_db)
        # self.modify(f1, action="random")
        # if game_in_db == True:
        #     message = "Selected game: {}.".format(game[0][1])
        #     self.boardgame = message_text
        #     self.update_message_chain(message, response_required=False, priority="high")
        #     self.modify(f1, action="game_selected")
        # elif game_in_db == False:
        #     req_yes_no = "{REQ:" + "Choice}"
        #     message = "Sorry, it seems like '{}' doesn't exist in the database. \
        #         The closest game I found is '{}'.  {}Do you want to continue with the suggested game?".format(message_text.capitalize(), closest_match[0].capitalize(), req_yes_no)
        #     self.update_message_chain(message, priority="high")
        #     self.modify(f1, action="game_selected")


    @Rule(AS.f1 << Fact(action="game_selected"),
        salience=98)
    def game_selected(self, f1):
        print("game selected facts", self.facts)
        self.update_message_chain("I can help provide almost anything for {} - specific information, instructions or reviews. What do you need?".format(self.boardgame.capitalize()), priority="low")
        self.modify(f1, action="game_journey")
    
    @Rule(AS.f1 << Fact(action="game_not_found"),
        salience=98)
    def game_not_found(self, f1):
        print("game not found facts", self.facts)
        self.update_message_chain("Please check how you spelled the game name and try again.", priority="low")
        self.modify(f1, action="path_choice")

    @Rule(Fact(action="suggest_game"),
        Fact(suggest_game = True),
        Fact(message_text=MATCH.message_text),
        salience = 98)
    def suggest_game(self, message_text):
        doc = self.process_nlp(message_text)
        #genre ,max_players, play_time, rating,
        # self.game_suggestion_journey = "gn_pl_pt_rt_"
        if 'gn_' in self.game_suggestion_journey:
            req_yes_no = "{REQ:" + "Choice}"
            if not self.ans_g:
                msg = "{}Let's start with 'Do you know what genre you are interested in?'"
                self.update_message_chain(msg.format(req_yes_no), priority="low")
            choice = self.check_yes_no(message_text)
            if choice:
                if choice.text == 'yes':
                    self.update_message_chain("Cool! You can specify up to three genres. Separate them by comma (',').", priority="high")
                    self.game_suggestion_journey = self.game_suggestion_journey.replace('gn_', '')
                elif choice.text == 'no':
                    self.update_message_chain("Alright, what about maximum number of players?", priority="high")
                    self.game_suggestion_journey = self.game_suggestion_journey.replace('gn_', 'gn')
            else:
                msg = "{}Please write 'yes' or 'no'. "
                self.update_message_chain(msg.format(req_yes_no), priority="low")
        




        

    @Rule(AS.f1 << Fact(action="game_journey"),
          Fact(message_text=MATCH.message_text),
          salience=99)
    def direct_action(self, f1, message_text):
        """

        """
        # print("FACTS:", self.knowledge)
        doc = self.process_nlp(message_text)
        # print out what the tokens are in the user input
        # print("HEEEEERRRRREEEEEE")
        # for token in doc:
        #     print(token.text, token.pos_, token.dep_, token.lemma_)
        print("message from user", message_text)
        
        matches = self.get_multiple_matches(doc, MultiTokenDictionary['game_info'])
        if len(matches) > 0:
            print("GAME INFO")
            self.update_message_chain("Game_info: Ok, let's get you informed!", response_required=False, priority="high")
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
        game_content = scrape(self.boardgame)
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
    

    def check_yes_no(self, message_text):
        choice = None
        doc = self.process_nlp(message_text.split(" ")[-1])
        if "{TAG:Yes/No}" in message_text:
            choice = self.get_multiple_matches(doc, MultiTokenDictionary['yes'])
            if (choice is None) or (type(choice) == str and (choice == '')):
                choice = self.get_multiple_matches(doc, MultiTokenDictionary['no'])
            elif (choice is None) or choice.text == '':
                choice = self.get_multiple_matches(doc, MultiTokenDictionary['no'])
        print("check_yes_no doc:", doc)
        print("^ choice: ", choice)
        if choice is not None:
            return choice


# r = ReasoningEngine()
# doc = r.process_nlp("{TAG:Yes/No} no")
# r.check_yes_no(doc, "{TAG:Yes/No} no")