import json
import re #REGEX
from urllib.request import urlopen
from bs4  import BeautifulSoup as soup
import requests
from DB import add_games_to_db

# from boardgamegeek import BGGClient

game_codes = {
    "monopoly" : "1406",
    "uno" : "2223",
    "scrabble" : "320",
    "domino dice" :"3805",
    "scythe" : "169786",
    "chess" : "171",


}

def get_game_code(game_name):
    for g, value in game_codes.items():
        if game_name in game_codes.keys():
            return game_codes[game_name]
        else:
            print("No such game found :(")
            return {"message" : "I couldn't find such game in our repertoire. Maybe try again?",
                    "response_required" : True}
    return None

def scrape(game_name):
    try:
        gamecode = get_game_code(game_name.lower())
    except Exception:
        print("can't find {} game code".format(game_name))
        return "Couldn't find the game code"
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

def add_data():
    response = requests.get('https://www.boardgamegeek.com/browse/boardgame')
    # url = "https://www.boardgamegeek.com/browse/boardgame"
    # page = urlopen(response)
    # html = response.read()
    scrape = soup(response.text, "html.parser")
    obj_name = scrape.find_all('tr', id="row_")
    all_games = []
    # Got all rows in the current file. Loop through to get individual object to be added to DB.
    for index, row in enumerate(obj_name, start=1):
        ratings = row.find_all(class_="collection_bggrating")
        rank = row.find(class_="collection_rank").get_text()
        name = row.find(id="results_objectname{}".format(index)).find("a").get_text()
        bgg_rank = ratings[0].get_text()
        average_rating = ratings[1].get_text()
        num_voters = ratings[2].get_text()
  
        game_object = {
            "rank": int(re.sub('[\n\t]' ,'',rank)),
            "name" : re.sub('[\n\t]' ,'',name),
            "bgg_rating": re.sub('[\n\t]' ,'',bgg_rank),
            "average_rating" : re.sub('[\n\t]' ,'',average_rating),
            "num_voters" : int(re.sub('[\n\t]' ,'',num_voters))
        }
        all_games.append(game_object)
    
    add_games_to_db(all_games)

    # collectionitems

add_data()