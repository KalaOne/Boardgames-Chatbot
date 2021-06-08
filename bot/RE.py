from experta import *
import spacy
from spacy.matcher import Matcher, PhraseMatcher
from .scraper import scrape
from .DB import connect_db, get_specific_game_from_db
import difflib
import re



MultiTokenDictionary = {
    "yes": [
        [{"LOWER": {"IN": ["yes", "yeah"]}}],
        [{"LOWER": {"IN": ["y", "yep", "yeh", "ye"]}}]
    ],
    "no": [
        [{"LOWER": {"IN": ["no", "n"]}}],
        [{"LOWER": {"IN": ["nope", "nah", "na"]}}]
    ],

    "specific" : [ 
        [{"LEMMA": {"IN": ["specific", "exact", "explicit", "precise"]}}],

    ],

    "general" : [ 
        [{"LEMMA": {"IN": ["general", "generic", "universal"]}}],

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
        [{"LEMMA": "assistance"}],
        [{"LOWER": "help"}]

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
                                'response_required': True, 'background' : False}
        self.message = []
        self.tags = ""
        self.game_data = None
        self.boardgame = None
        #genre ,max_players, play_time, rating,
        self.game_suggestion_journey = "gn_pl_pt_rt_"
        self.ans_g = self.ans_p = self.ans_t = self.specific_info_question = False
        self.ask1 = False
        self.background = False
        self.background_image = None

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

    def update_message_chain(self, message, priority = "high", response_required = True, background = False):
        """
        priority == high - first message
        priority == low - at the end of the stack.
        """
        if (len(self.message) == 1 and
                self.default_message in self.message and
                priority != 7):
            self.message = []
        if priority == "low":
            self.message.append({'message' : message, 'response_required' : response_required, 'background' : background})
        elif priority == "high":
            self.message.insert(0, {'message' : message, 'response_required' : response_required, 'background' : background})
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
            self.update_message_chain("I have access to over 250,000 games. I can help you get specific information about a particular game or \
                suggest a game based on your requirements.", response_required=False)
            self.update_message_chain("What do you want me to do?", priority="low")
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
                if game:
                    # the specified game is in DB
                    message = "Selected game: <b>{}</b>.".format(game[0][1])
                    self.boardgame = game[0]
                    self.background_image = game[0][4]
                    self.update_message_chain(message, response_required=False, priority="high", background=self.background_image)
                    self.modify(f1, action="game_selected")
                else: 
                    # Game is not in DB. Suggest alternative
                    req_yes_no = "{REQ:" + "Choice}"
                    choice = None
                    if not self.ask1:
                        message = "Sorry, it seems that <b>'{}'</b> doesn't exist in the database. \
                            The closest game I found is <b>'{}'</b>. ".format(message_text.capitalize(), closest_match[0][1].capitalize())
                        message2 = "{}Do you want to continue with the suggested game?".format(req_yes_no)
                        self.boardgame = closest_match[0]
                        self.background_image = closest_match[0][4]
                        self.update_message_chain(message, priority="low", response_required=False)
                        self.update_message_chain(message2, priority="low")
                        self.ask1 = True
                    choice = self.check_yes_no(message_text)
                    if choice:
                        if choice.text == 'yes':
                            self.modify(f1, action="game_selected")
                        elif choice.text == 'no':
                            self.update_message_chain("Okay. Then please re-type the game you're interested in.", priority="high")
                            self.ask1 = False
                        else:
                            msg = "{}Please write 'yes' or 'no'. "
                            self.update_message_chain(msg.format(req_yes_no), priority="low")
                            self.modify(f1, action="path_choice")
                    else:
                        msg = "{}Please write 'yes' or 'no'. "
                        self.update_message_chain(msg.format(req_yes_no), priority="low")
                        
                        


    @Rule(AS.f1 << Fact(action="game_selected"),
        salience=98)
    def game_selected(self, f1):
        self.update_message_chain("I can help provide almost anything for <b>{}</b> - information, playtime, creators, artists,\
             number of players required, game rating, you name it! What do you want to know?".format(self.boardgame[1].capitalize())
            , priority="low", background=self.background_image)
        self.modify(f1, action="game_journey")
 

    @Rule(Fact(action="suggest_game"),
        AS.f2 << Fact(suggest_game = True),
        Fact(message_text=MATCH.message_text),
        salience = 98)
    def suggest_game(self, f2, message_text):
        doc = self.process_nlp(message_text)
        req_yes_no = "{REQ:" + "Choice}"
        if not self.specific_info_question:
            msg = "{}Do you know any information that could help the suggestion?"
            self.update_message_chain(msg.format(req_yes_no), priority="low")
            self.specific_info_question = True
        choice = self.check_yes_no(message_text)
        if choice:
            if choice.text == 'yes':
                self.update_message_chain("Noice! What specific information do you know? Separate the categories with a comma ','", response_required=False)
                self.declare(Fact(suggest_known_info=True))
                self.modify(f2, suggest_game = False)
                
            elif choice.text == 'no':
                self.update_message_chain("I'll ask you a few questions to help narrow down games to suggest.", priority="high", response_required=False)
                self.modify(f2, suggest_game = False)
                self.declare(Fact(suggest_known_info=False))
        elif not choice:
            if not self.specific_info_question:
                msg = "Suggest_game: {}Please write 'yes' or 'no'. "
                self.update_message_chain(msg.format(req_yes_no), priority="low")

    @Rule(Fact(action="suggest_game"),
        # Fact(suggest_game = True),
        Fact(suggest_known_info=True),
        Fact(message_text=MATCH.message_text),
        salience = 97)
    def suggest_game_user_info(self, message_text):
        print("User is going to provide information they know. We extract it here and search DB from it")
        self.update_message_chain("Say something I'm givbing up on you...", priority="low")


    @Rule(Fact(action="suggest_game"),
        # Fact(suggest_game = True),
        Fact(suggest_known_info=False),
        Fact(message_text=MATCH.message_text),
        salience = 96)
    def suggest_game_general_info(self, message_text):
        print("User doesn't know shit. We extract general information from them NOW. Display games after that. Hehehee")
        
        #genre ,max_players, play_time,
        # self.game_suggestion_journey = "gn_pl_pt_"
        # if 'gn_' in self.game_suggestion_journey:
        #     req_yes_no = "{REQ:" + "Choice}"
        #     if not self.ans_g:
        
        msg = "Let's start with <b>genre</b>. What genre are you interested in? You can specify up to 3 genres.\
                    Separate them by comma ','."
        self.update_message_chain("Let's start with <b>genre</b>. What genre are you interested in? You can specify up to 3 genres.\
                    Separate them by comma ','.", priority="low", response_required=True)
                

            # choice = self.check_yes_no(message_text)
        #     if choice:
        #         if choice.text == 'yes':
        #             self.update_message_chain("Cool! You can specify up to three genres. Separate them by comma (',').", priority="high")
        #             self.game_suggestion_journey = self.game_suggestion_journey.replace('gn_', '')
        #         elif choice.text == 'no':
        #             self.update_message_chain("Alright, what about maximum number of players?", priority="high")
        #             self.game_suggestion_journey = self.game_suggestion_journey.replace('gn_', 'gn')
        #     else:
        #         msg = "{}Please write 'yes' or 'no'. "
        #         self.update_message_chain(msg.format(req_yes_no), priority="low")
        

     

    @Rule(AS.f1 << Fact(action="game_journey"),
          Fact(message_text=MATCH.message_text),
          salience=99)
    def game_information_journey(self, f1, message_text):
        # print("FACTS:", self.knowledge)
        doc = self.process_nlp(message_text)
        # print out what the tokens are in the user input
        # print("HEEEEERRRRREEEEEE")
        # for token in doc:
        #     print(token.text, token.pos_, token.dep_, token.lemma_)
        info_type_tag = "{REQ:" + "InfoType}"
        matches = self.get_multiple_matches(doc, MultiTokenDictionary['game_info'])
        if len(matches) > 0:
            print("GAME INFO")
            self.update_message_chain("Game_info: Ok, let's get you informed!", response_required=False, priority="high")
            # self.update_message_chain("{}Do you need specific or general information about {}?".format(info_type_tag, self.boardgame[1]), "low", True)
            self.modify(f1, action="information")
            self.declare(Fact(info_type=False))
           
        else:
            matches = self.get_multiple_matches(doc, MultiTokenDictionary['play_instructions'])
            if (len(matches) > 0) :
                self.update_message_chain("Instructions: Cool, here's how to play Chess!", response_required=False, priority="high")
                self.update_message_chain("You move X to Y and then Z goes AAAAAA!", priority = "low")
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
        Fact(message_text=MATCH.message_text),
            salience=95)
    def determine_info_type(self, message_text):
        info_type_tag = "{REQ:" + "InfoType}"
        self.update_message_chain("{}Do you need specific or general information about {}?".format(info_type_tag, self.boardgame[1]), "low", True)
        print("Decide if specific of general information ", message_text)
        info_type = self.check_info_type(message_text)
        print("Information type after function call: ", info_type)
        if(info_type):
            if info_type.text == 'specific':
                self.declare(Fact(info_type = "specific"))
            elif info_type.text == 'general':
                self.declare(Fact(info_type = "general"))
            else:
                self.update_message_chain("Sorry, that wasn't successful. Specify generic or specific information", priority="low")


    @Rule(Fact(action="information"),
        Fact(info_type="specific"),
         salience= 92)
    def provide_specific_info(self):
        print("SPECIFIC INFORMATION")
        self.update_message_chain("Okay, what exactly do you want to know?", response_required=True, priority ="low")
       


    @Rule(Fact(action="information"),
        Fact(info_type="general"),
         salience= 91)
    def provide_general_info(self):
        print("GENERAL INFO")
        self.update_message_chain("Alright. Showing you description, minimum-maximum number of players, playing time, \
            recommended age.", priority="low", response_required=False)
        message = "<ul class='general_game_info'> \
                <li> Name: {} </li><br>\
                <li> Description: {} </li>\
                <li> Players: {} - {} </li>\
                <li> Playing time: {} </li> \
                <li> Age: {} </li> </ul>"
        strings_to_replace = [
            ('<[^<]+?/>', ''),
            ('<.*?>', ''),
            ('&quot;', '"'),
            ('&rsquo;', "'"),
            ('&ndash;', '-'),
            ('&ldquo;', '"'),
            ('&rdquo;', '"'),
        ]
        for old, new in strings_to_replace:
            print(old, new)
            description = re.sub(old, new, self.boardgame[2])
        print(description)


            
        # self.update_message_chain("General information about {}.".format(game_content['name']), response_required=False, priority="low")
        # self.update_message_chain(game_content['description'], response_required=False, priority="low")
        # self.update_message_chain("Would you like to know anything else?", priority="low")
        # self.declare(Fact(more_info_needed = True))


    @Rule(Fact(action="specific_information"), 
        Fact(message_text=MATCH.message_text),
        salience = 90)
    def provide_specific_infor(self, message_text):
        print("SPECIFIC INFORMATION INCOMING!")

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
        if choice is not None:
            return choice
        return choice

    def check_info_type(self, message_text):
        info_type = None
        doc = self.process_nlp(message_text.split(" ")[-1])
        if "{TAG:S/G}" in message_text:
            info_type = self.get_multiple_matches(doc, MultiTokenDictionary['specific'])
            if (info_type is None) or (type(info_type) == str and (info_type == '')):
                info_type = self.get_multiple_matches(doc, MultiTokenDictionary['general'])
            elif (info_type is None) or info_type.text == '':
                info_type = self.get_multiple_matches(doc, MultiTokenDictionary['general'])
        print("Info_type: ", info_type)
        if info_type is not None:
            return info_type

# r = ReasoningEngine()
# doc = r.process_nlp("{TAG:Yes/No} no")
# r.check_yes_no(doc, "{TAG:Yes/No} no")