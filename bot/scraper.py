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
    print(gamecode)
    url = ("https://www.boardgamegeek.com/xmlapi/boardgame/{}".format(gamecode))
    webpage = urlopen(url)
    html = webpage.read()
    page_scrape = soup(html, "html.parser")
    game_info = page_scrape.find("description")

    print(game_info)
    return "Heyyayaya"



a = scrape("CHESS")
print(a)