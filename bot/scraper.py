import json
import re #REGEX
from urllib.request import urlopen
from bs4  import BeautifulSoup as soup

game_codes = {
    "chess" : "171",
    "monopoly" : "1406",
    "uno" : "2223",
    "scrabble" : "320",
    "domino dice" :"3805",


}

def get_game_code(game_name):
    for g, value in game_codes.items():
        if g in game_codes.keys():
            return value
    else:
        print("No such game found :(")
        return {"message" : "I couldn't find such game in our repertoire. Maybe try again?",
                "response_required" : True}

def scrape(game_name):
    
    gamecode = get_game_code(game_name.lower())
    print("gamecode: ",gamecode)
    game_content = []
    url = ("https://www.boardgamegeek.com/xmlapi/boardgame/{}".format(gamecode))
    webpage = urlopen(url)
    html = webpage.read()
    page_scrape = soup(html, "html.parser")
    game_name = page_scrape.find("name", {"primary":"true"}).get_text()
    game_description = page_scrape.find("description").get_text()
    min_players = page_scrape.find("minplayers").get_text()
    max_players = page_scrape.find("maxplayers").get_text()
    min_play_time = page_scrape.find("minplaytime").get_text()
    max_play_time = page_scrape.find("maxplaytime").get_text()
    age = page_scrape.find("age").get_text()
   
    game_object = {
        'name' : game_name,
        'description' : game_description,
        'min_players' : min_players,
        'max_players' : max_players,
        'play_time' : min_play_time + " - " + max_play_time,
        'age' : age
    }
    # js.Write() takes html. Can write the whole div here and send it to be written.
    return game_object



# a = scrape("CHESS")
# print(a)