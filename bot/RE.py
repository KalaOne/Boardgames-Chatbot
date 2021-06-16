from experta import *
import spacy
from spacy.matcher import Matcher, PhraseMatcher
from .scraper import scrape
from .DB import *
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
        self.default_message = {'message': "Default: I'm sorry. I don't know how to help with that just yet. Please refresh the page",
                                'response_required': True, 'background' : False}
        self.message = []
        self.tags = ""
        self.game_data = None
        self.boardgame = None
        self.suggest_game_genres = None
        self.suggest_game_players = None
        self.suggest_game_time = None
        self.info_type = None
        self.known_categories = {
            "yearpublished" : "",
            "maxplayers" : "",
            "playingtime" : "",
            "category0" : ""
        }
        self.game_dict_populated = False
        
        self.ans_g = self.ans_p = self.ans_t = False
        self.ask_p = self.ask_g = self.ask_t = self.specific_info_question = self.general_or_specific = False 

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
                    self.update_message_chain(message, priority="low", response_required=False, background=self.background_image)
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
                        
                        
## SPECIFIC GAME INFORMATION JOURNEY BELOW

    @Rule(AS.f1 << Fact(action="game_selected"),
        salience=98)
    def game_selected(self, f1):
        info_type_tag = "{REQ:" + "InfoType}"
        self.update_message_chain("I can help provide almost anything for <b>{}</b> - game information, playtime, creators, artists,\
            number of players required, game rating, you name it!".format(self.boardgame[1].capitalize())
            , priority="low", response_required=False, background=self.background_image)
        self.update_message_chain("{}Do you need <u>specific</u> or <u>general</u> information about {}?".format(info_type_tag, self.boardgame[1]), priority="low")
        self.modify(f1, action="information")
 

    @Rule(Fact(action="information"),
        Fact(message_text=MATCH.message_text),
            salience=95)
    def determine_info_type(self, message_text):
        self.check_info_type(message_text)
        if(self.info_type):
            if self.info_type == 'specific':
                self.general_or_specific = True
                self.declare(Fact(info_type = "specific"))
            elif self.info_type == 'general':
                self.general_or_specific = True
                self.declare(Fact(info_type = "general"))
            else:
                self.general_or_specific = False
                self.update_message_chain("Sorry, that wasn't successful. Specify generic or specific information", priority="low")


    @Rule(Fact(action="information"),
        Fact(info_type="specific"),
         salience= 95)
    def provide_specific_info(self):
        spec_cat_tag = "{REQ:"+"SPEC_CAT}"
        self.update_message_chain("Okay, indicate what specific information you are looking for? If more than one category, separate then by comma ','", 
                response_required=True, priority ="low")

       

## General information journey below 
    @Rule(AS.act << Fact(action="information"),
        Fact(info_type="general"),
         salience= 91)
    def provide_general_info(self, act):
        print("CURRENT BOARDGAME", self.boardgame)
        self.update_message_chain("Alright. Showing you description, minimum-maximum number of players, playing time, \
            and recommended age.", priority="low", response_required=False)
        message = "<ul class='general_game_info'> \
                <li> Name: {} </li>\
                <li> Players: {} - {} </li>\
                <li> Playing time: {} minutes </li> \
                <li> Age: {} </li> <br>\
                <li> Description: {} </li></ul>"
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
            description = re.sub(old, new, self.boardgame[2])
        self.update_message_chain(message.format(self.boardgame[1], self.boardgame[17].split(".")[0],
            self.boardgame[18].split(".")[0], self.boardgame[19].split(".")[0], self.boardgame[22],description), 
            priority="low", response_required=False)
        self.update_message_chain("I hope this satisfies your needs. Thanks for stopping by!", priority="low", response_required=False)
        self.modify(act, action='finish_it')


## SUGGEST A JOURNEY GAME BELOW

    @Rule(Fact(action="suggest_game"),
        AS.f2 << Fact(suggest_game = True),
        Fact(message_text=MATCH.message_text),
        salience = 98)
    def suggest_game0(self, f2, message_text):
        doc = self.process_nlp(message_text)
        req_yes_no = "{REQ:" + "Choice}"
        if not self.specific_info_question:
            msg = "{}Do you know any information that could help the suggestion? (yes/no)"
            self.update_message_chain(msg.format(req_yes_no), priority="low")
            self.specific_info_question = True
        choice = self.check_yes_no(message_text)
        if choice:
            if choice.text == 'yes':
                ask_categories = "{REQ:"+"CATEGORY}"
                message = "{}What specific information do you know? Separate the categories with a comma ','"
                self.update_message_chain(message.format(ask_categories), response_required=True)
                self.declare(Fact(suggest_known_info=True))
                self.modify(f2, suggest_game = False)

            elif choice.text == 'no':
                self.update_message_chain("I'll ask you a few questions to help narrow down games to suggest.", response_required=False)
                self.modify(f2, suggest_game = False)
                self.declare(Fact(suggest_known_info=False))
        elif not choice:
            if not self.specific_info_question:
                msg = "Suggest_game: {}Please write 'yes' or 'no'. "
                self.update_message_chain(msg.format(req_yes_no), priority="low")

## Yes journey below ##
    @Rule(AS.act << Fact(action="suggest_game"),
        Fact(suggest_known_info=True),
        Fact(message_text=MATCH.message_text),
        salience = 97)
    def suggest_game_user_info(self,act, message_text):
        self.get_known_categories(message_text)
        if self.game_dict_populated:
            self.update_message_chain("Alrighty! Here are the top 10 games that match your request.", priority="low", response_required=False)
            games_to_show = pull_suggested_game_with_background_info(self.known_categories)
            if games_to_show:
                games_display = """ <ol class='ten-games-list'>"""
                for g in games_to_show:
                    games_display += '<li>{}</li>'.format(g[1])
                games_display += "</ol>"
                self.update_message_chain(games_display, priority="low", response_required=False)
            self.update_message_chain("I hope this satisfies your needs. Thanks for stopping by!", priority="low", response_required=False)
            self.modify(act, action='finish_it')
        # self.update_message_chain("Say something I'm givbing up on you...", priority="low")

## No journey below ##
    @Rule(Fact(action="suggest_game"),
        Fact(suggest_known_info=False),
        Fact(message_text=MATCH.message_text),
        salience = 96)
    def suggest_game(self, message_text):
        ask_genre = "{REQ:" + "GENRE}"
        if not self.ask_g:
            msg = "{}Let's start with <b>genre</b>. What genre are you interested in? You can specify up to 3 genres.\
                        Separate them by comma ','."
            self.update_message_chain(msg.format(ask_genre), priority="low", response_required=True)
            self.ask_g = True
        if self.ask_g:
            genres = self.get_genre(message_text)
            if genres:
                genres = genres.split(",")
                self.ans_g = True
        if self.suggest_game_genres is None and self.ans_g:
            self.suggest_game_genres = genres

    @Rule(Fact(action="suggest_game"),
        Fact(suggest_known_info=False),
        Fact(message_text=MATCH.message_text),
        salience = 95)
    def suggest_game1(self, message_text):
        ask_players = "{REQ:"+ "NUM_PLAYERS}"
        if not self.ask_p:
            msg = "{}How about number of players? E.g. 2-4."
            self.update_message_chain(msg.format(ask_players), priority="low", response_required=True)
            self.ask_p = True
        if self.ask_p:
            players = self.get_num_players(message_text)
            if players:
                players = players.split("-")
                self.ans_p = True
        if self.suggest_game_players is None and self.ans_p:
            self.suggest_game_players = players

    
    @Rule(AS.f1 << Fact(action="suggest_game"),
        Fact(suggest_known_info=False),
        Fact(message_text=MATCH.message_text),
        salience = 94)
    def suggest_game2(self,f1, message_text):
        ask_time = "{REQ:"+"PLAY_TIME}"
        if not self.ask_t:
            msg = "{}Roughly how long do you expect to play a game (in minutes)?"
            self.update_message_chain(msg.format(ask_time), priority="low", response_required=True)
            self.ask_t = True
        if self.ask_t:
            time = self.get_play_time(message_text)
            if time:    
                print("time:::", time)
                if "-" in time:
                    time = time.split("-")
                self.ans_t = True
        if self.suggest_game_time is None and self.ans_t:
            print("COMING IN HERE BEBEEEEEEEEEE")
            self.suggest_game_time = time
            self.modify(f1, action="pull_suggest_game")
    

    @Rule(AS.act << Fact(action='pull_suggest_game'),
        salience = 99)
    def genre_collection(self, act):
        self.update_message_chain("Okay, here are top 10 games that match your request.", priority="high", response_required=False)
        games_to_show = pull_suggested_game_no_background_info(self.suggest_game_genres, self.suggest_game_players, self.suggest_game_time)
        games_display = """ <ol class='ten-games-list'>"""
        for g in games_to_show:
            games_display += '<li>{}</li>'.format(g[1])
        
        games_display += "</ol>"
        self.update_message_chain(games_display, priority="low", response_required=False)
        self.update_message_chain("I hope this satisfies your needs. Thanks for stopping by!", priority="low", response_required=False)
        self.modify(act, action='finish_it')


    @Rule(Fact(action='finish_it'),
        salience = 98)
    def finish_it(self):
        self.update_message_chain("Okay, you can go now.", priority="low", response_required=True)


## Specific game selected below ##
    # @Rule(AS.f1 << Fact(action="game_journey"),
    #       Fact(message_text=MATCH.message_text),
    #       salience=99)
    # def game_information_journey(self, f1, message_text):
    #     # print("FACTS:", self.knowledge)
    #     doc = self.process_nlp(message_text)
    #     # print out what the tokens are in the user input
    #     # print("HEEEEERRRRREEEEEE")
    #     # for token in doc:
    #     #     print(token.text, token.pos_, token.dep_, token.lemma_)
    #     info_type_tag = "{REQ:" + "InfoType}"
    #     matches = self.get_multiple_matches(doc, MultiTokenDictionary['game_info'])
    #     if len(matches) > 0:
    #         print("GAME INFO")
    #         self.update_message_chain("Ok, let's get you informed!", response_required=False, priority="high")
    #         self.update_message_chain("{}Do you need <u>specific</u> or <u>general</u> information about {}?".format(info_type_tag, self.boardgame[1]), "low", True)
            
    #         self.modify(f1, action="information")
        # else:
        #     matches = self.get_multiple_matches(doc, MultiTokenDictionary['play_instructions'])
        #     if (len(matches) > 0) :
        #         self.update_message_chain("Instructions: Cool, here's how to play Chess!", response_required=False, priority="high")
        #         self.update_message_chain("You move X to Y and then Z goes AAAAAA!", priority = "low")
        #         self.declare(Fact(instructions = True))
        #         self.modify(f1, action="instructions")
        #     else:
        #         matches = self.get_multiple_matches(doc, MultiTokenDictionary['reviews'])
        #         if (len(matches) > 0) :
        #             print("Reviews")
        #             self.update_message_chain("Reviews: This game has some nice reviews. Check this out:", response_required=False, priority="high")
        #             self.update_message_chain("<strong>Very nice game!</strong>", response_required=False, priority="low")
        #             self.modify(f1, action="reviews")
        #             self.declare(Fact(reviews = True))
    # 
    # if (len(matches) > 0) :
    #     self.update_message_chain("(M)Reviews: This game has some nice reviews. Check this out:", response_required="Random")
    #     self.update_message_chain("<strong>Very nice game!</strong>", priority=0)
    # else:
    #     print("AH HELL NAW!")
        

    


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
        if "{TAG:S/G}" in message_text:
            if ('specific' or 'exact' or 'explicit' or 'precise') in message_text:
                self.info_type = 'specific'
            elif ('general' or 'generic' or 'universal') in message_text:
                self.info_type = 'general'
            else:
                print("Neither specific or generic information.")
                

        

    def get_genre(self, message_text):
        genre = None
        if "{TAG:GENRE}" in message_text:
            tag, genre = message_text.split("{TAG:GENRE} ")
        return genre
    
    def get_num_players(self, message_text):
        num_players = None
        if "{TAG:PLAYERS}" in message_text:
            tag, num_players = message_text.split("{TAG:PLAYERS} ")
        return num_players

    def get_play_time(self, message_text):
        time = None
        if "{TAG:TIME}" in message_text:
            tag, time = message_text.split("{TAG:TIME} ")
        return time

    def get_known_categories(self, message_text):
        input_categories = message_text.split(",")
        for cat in input_categories:
            # Getting the published year
            
            if ('publish' or 'published') in cat:
                words = cat.split()
                for word in words:
                    if str.isdigit(word):
                        print("yearpublished word is digit:", word)
                        if self.known_categories["yearpublished"] == "":
                            self.known_categories["yearpublished"] = word + ".0"
                            break
            # Getting the number of players
            elif ('player' or 'players') in cat:
                words = cat.split()
                for word in words:
                    if str.isdigit(word):
                        print("players word is digit:", word)
                        if self.known_categories["maxplayers"] == "":
                            self.known_categories["maxplayers"] = str(word) + ".0"
                            break
            # Get playing time
            elif ('time' or 'playtime' or 'timer') in cat:
                words = cat.split()
                for word in words:
                    minutes = 0
                    if str.isdigit(word):
                        print("time entered:", word)
                        if len(word) == 1:
                            minutes = int(word)
                            minutes *= 60
                            print("time converted to mins:", minutes)
                        if minutes != 0:
                            if self.known_categories["playingtime"] == "":
                                self.known_categories["playingtime"] = str(minutes) + ".0"
                        else:
                            if self.known_categories["playingtime"] == "":
                                self.known_categories["playingtime"] = word + ".0"
                        break
            # Getting Genre
            elif ('genre' or 'category') in cat:
                cat = cat.split()
                print("category final word:", cat[-1])
                self.known_categories["category0"] = cat[-1]
            else:
                words = cat.split()
                for w in words:
                    print(w)
                print("SOM TING WONG. Unable to find described words in the sentence. hmmm")
        if self.known_categories["playingtime"] != "" and self.known_categories["maxplayers"] != "" and self.known_categories["yearpublished"] != ""\
            and self.known_categories["category0"] != "":
            self.game_dict_populated = True

        ##Need to replace the user categories with ones in the DB - genre with category0-1-2-3
        ## Check other things that might need replacing. Author or whatever.

    def get_specific_information(self, message_text):
        if "{TAG:SPECIFIC_CATEGORY}" in message_text:
            print("yeaaaah!")

# r = ReasoningEngine()
# r.get_known_categories('I\'m looking for a game published in 2011, maximum players are 6, playtime = 2 hours, genre is medieval')
# "yearpublished" : "",
#             "maxplayers" : "",
#             "playingtime" : "",
#             "category0" : ""