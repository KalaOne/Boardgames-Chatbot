import psycopg2
import psycopg2.extras
from datetime import datetime
import pandas as pd
import csv
import numpy as np
from fuzzywuzzy import fuzz
import re
import math
from difflib import SequenceMatcher
import string


conn = psycopg2.connect(host='localhost', port=5433, user='postgres', password='postgres')

def connect_db():
    # conn = psycopg2.connect("dbname=postgres user=postgres password=postgres")
    
    cur = conn.cursor()
    cur.execute("SELECT * FROM my_games")
    games_list = cur.fetchall()

    cur.close()
    conn.close()
    return games_list


def add_games_to_db():
    #
    # Uses BGG_data file to add it all into the DB
    #

    start = datetime.now()
    s_time = start.strftime("%H:%M:%S")
    print("DB adding started at :", s_time)

    cur = conn.cursor()

    df = pd.read_csv('E:/basic_data.csv', lineterminator='\n', error_bad_lines=False)

    df_col = list(df)
    columns = ",".join(df_col)
    values = "VALUES({})".format(",".join(["%s" for _ in df_col]))
    insert = "INSERT INTO big_bgg_data ({}) {}".format(columns,values)
    try:
        psycopg2.extras.execute_batch(cur, insert, df.values)
    except psycopg2.DatabaseError as e:
        print("Unable.", e)
    conn.commit()

    end = datetime.now()
    e_time = end.strftime("%H:%M:%S")
    print("DB addition ended at: ", e_time)

    cur.close()
    conn.close()


def get_similar_names_from_db(game_name):
    """
        Given a board game name, searches through database for similar names.

        Returns:
            Closest game name + column location of the name
    """
    closest_name = None
    closest_name_under_70 = None
    cur = conn.cursor()
    match_ratio = 0

    try:
        all_names_query = "SELECT name0, name1, name2, name3, name4, name5, name6, name7, name8, name9 FROM bgg_data"
        cur.execute(all_names_query)
        all_names = cur.fetchall()
    except psycopg2.DatabaseError as e:
        print(e)
    df = pd.DataFrame(all_names)
 
    if not df.empty:
        for row in df.values:
            for i, name in enumerate(row):
                if name != 'NaN':
                    if (fuzz.ratio(name.lower(), game_name.lower()) > match_ratio):
                        match_ratio = fuzz.ratio(name.lower(), game_name.lower())
                        closest_name_under_70 = name
                    # if (SequenceMatcher(lambda x: x == " ", name.lower(), game_name.lower()).ratio() > match_ratio):
                    #     match_ratio = SequenceMatcher(lambda x: x == " ", name.lower(), game_name.lower()).ratio()
                else:
                    continue
                if match_ratio >= 85:
                    closest_name = [i, name]
                    break
    else:
        print("No game found in DB.")
    cur.close()       
    return closest_name, closest_name_under_70
    

def get_data_from_db_based_on_name(game_name):
    # Get all relevant information for particular game, given it's name
    # Returns: data row for game with similar name.
    the_game, close_game = get_similar_names_from_db(game_name)
    game_data = None
    cur = conn.cursor()
    if the_game:
        try:
            row_data_query = "SELECT name0_alt,name1,average,usersrated,minplayers,maxplayers,playingtime,minplaytime,maxplaytime, \
                yearpublished,boardgamerank,designer0,artist0,artist1,subdomain0,category0,category1,category2, \
                honor0,honor1,expansion0,expansion1,expansion2,description,thumbnail\
                        FROM bgg_data WHERE name{} = '{}'".format(the_game[0],the_game[1])
            cur.execute(row_data_query)
            game_data = cur.fetchall()
        except psycopg2.DatabaseError as e:
            print(e)
            return e
    else:
        return the_game, close_game

    # clean_description = re.sub('<[^<]+?>', '', game_data[0][21])
 

    cur.close()

    return game_data, close_game


def get_similar_name(game_name):
    closest_name = None
    closest_name_under_70 = None
    cur = conn.cursor()
    match_ratio = 0

    try:
        all_names_query = "SELECT name FROM big_bgg_data"
        cur.execute(all_names_query)
        all_names = cur.fetchall()
    except psycopg2.DatabaseError as e:
        print(e)
    # df = pd.DataFrame(all_names)

    if all_names:
        for name in all_names:
            if (fuzz.ratio(name[0].lower(), game_name.lower()) > match_ratio):
                match_ratio = fuzz.ratio(name[0].lower(), game_name.lower())
                closest_name_under_70 = name
            # if (SequenceMatcher(lambda x: x == " ", name.lower(), game_name.lower()).ratio() > match_ratio):
            #     match_ratio = SequenceMatcher(lambda x: x == " ", name.lower(), game_name.lower()).ratio()
            else:
                continue
            if match_ratio >= 85:
                closest_name = name
                break
    else:
        print("No game found in DB.")
    cur.close()       
    return closest_name, closest_name_under_70

def get_specific_game_from_db(game_name):
    the_game, close_game = get_similar_name(game_name)
    game_data = None
    close_game_data = None
    cur = conn.cursor()
    if the_game:
        try:
            row_data_query = "SELECT * FROM big_bgg_data WHERE name = '{}'".format(the_game[0])
            cur.execute(row_data_query)
            game_data = cur.fetchall()
        except psycopg2.DatabaseError as e:
            print(e)
            return e
    else:
        try:
            row_data_query = "SELECT * FROM big_bgg_data WHERE name = '{}'".format(close_game[0])
            cur.execute(row_data_query)
            close_game_data = cur.fetchall()
        except psycopg2.DatabaseError as e:
            print(e)
            return e

    # clean_description = re.sub('<[^<]+?>', '', game_data[0][2])
    # print(clean_description)

    cur.close()

    return game_data, close_game_data

def pull_suggested_game_no_background_info(genre, players, playtime):
    num_genre = len(genre)
    min_players = players[0]
    max_players = players[1]
    cur = conn.cursor()

    print("Genre coming in:", genre)
    print("Players coming in:", players)
    print("Time coming in:", playtime)
    print("Is time array?", isinstance(playtime, list))
    
    if num_genre > 0:
        if num_genre == 1:
            if not isinstance(playtime, list):
                query = """SELECT description, boardgamerank FROM bgg_data WHERE category0='{}' and \
                    minplayers='{}.0' and maxplayers='{}.0' and playingtime='{}.0' \
                        order by boardgamerank""".format(string.capwords(genre[0]), min_players, max_players, playtime)
            elif isinstance(playtime, list):
                query = """SELECT description, boardgamerank FROM bgg_data WHERE category0='{}' and \
                    minplayers='{}.0' and maxplayers='{}.0' and minplaytime='{}.0' and maxplaytime='{}.0' \
                        order by boardgamerank""".format(string.capwords(genre[0]), min_players, max_players, playtime[0], playtime[1])

        elif num_genre == 2:
            if not isinstance(playtime, list):
                query = """SELECT description, boardgamerank FROM bgg_data WHERE category0='{}' and category1='{}'\
                    and minplayers='{}.0' and maxplayers='{}.0' and playingtime='{}.0' \
                        order by boardgamerank""".format(string.capwords(genre[0]),string.capwords(genre[1]), min_players, max_players, playtime)
            elif isinstance(playtime, list):
                    query = """SELECT description, boardgamerank FROM bgg_data WHERE category0='{}' and category1='{}'\
                    and minplayers='{}.0' and maxplayers='{}.0' and minplaytime='{}.0' and maxplaytime='{}.0' \
                        order by boardgamerank""".format(string.capwords(genre[0]),string.capwords(genre[1]), min_players, max_players, playtime[0], playtime[1])
        elif num_genre == 3:
            if not isinstance(playtime, list):
                query = """SELECT description, boardgamerank FROM bgg_data WHERE category0='{}' and category1='{}'\
                and category2='{}' and minplayers='{}.0' and maxplayers='{}.0' and playingtime='{}.0' \
                        order by boardgamerank""".format(string.capwords(genre[0]),string.capwords(genre[1]),
                        string.capwords(genre[2]), min_players, max_players, playtime)
            elif isinstance(playtime, list):
                    query = """SELECT description, boardgamerank FROM bgg_data WHERE category0='{}' and category1='{}'\
                and category2='{}' and minplayers='{}.0' and maxplayers='{}.0' and minplaytime='{}.0' and maxplaytime='{}.0' \
                        order by boardgamerank""".format(string.capwords(genre[0]),string.capwords(genre[1]), 
                        string.capwords(genre[2]), min_players, max_players, playtime[0], playtime[1])
    try:
        cur.execute(query)
        descriptions = cur.fetchmany(10)
    except psycopg2.DatabaseError as e:
        print(e)
        return e
    
    ten_games = []
    current_game = None
    for game in descriptions:
        words = game[0].split()
       
        final_sentence = sentence = words[1] + " " + words[2] + " " + words[3] + " " + words[4] + " " + words[5]
        if "'" in sentence:
            index = sentence.find("'")
            final_sentence = sentence[:index] + "'" + sentence[index:]
        new_game_query = """SELECT * FROM big_bgg_data WHERE description LIKE '%{}%' \
            """.format(final_sentence)
        try:
            cur.execute(new_game_query)
            current_game = cur.fetchone()
        except psycopg2.DatabaseError as e:
            print(e)
            
        
        if current_game:
            ten_games.append(current_game)
        else:
            print("pull_data_for_suggested_game: No game has been added. Who knows, query might be wrong....")
        
    return ten_games

def pull_suggested_game_with_background_info(category_dict):
    print(category_dict)
    cur = conn.cursor()

    query = """ select description, boardgamerank from bgg_data where category0='{}' and maxplayers='{}'
            and yearpublished='{}' and playingtime='{}'
            """.format(string.capwords(category_dict["category0"]),category_dict["maxplayers"],
                    category_dict["yearpublished"],category_dict["playingtime"])

    try:
        cur.execute(query)
        descriptions = cur.fetchmany(10)
    except psycopg2.DatabaseError as e:
        print(e)
        return e

    ten_games = []
    current_game = None
    for game in descriptions:
        words = game[0].split()
       
        final_sentence = sentence = words[1] + " " + words[2] + " " + words[3] + " " + words[4] + " " + words[5]
        if "'" in sentence:
            index = sentence.find("'")
            final_sentence = sentence[:index] + "'" + sentence[index:]
        new_game_query = """SELECT * FROM big_bgg_data WHERE description LIKE '%{}%' \
            """.format(final_sentence)
        try:
            cur.execute(new_game_query)
            current_game = cur.fetchone()
        except psycopg2.DatabaseError as e:
            print(e)
            
        
        if current_game:
            ten_games.append(current_game)
        else:
            print("pull_data_for_suggested_game: No game has been added. Who knows, query might be wrong....")
        
    return ten_games
    


def get_db_column_names(db_name):
    print("Searching DB name:", db_name)
    db_columns = None
    cur = conn.cursor()
    query = """ SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name   = '{}';""".format(db_name)
    try:
        cur.execute(query)
        db_columns = cur.fetchall()
    except psycopg2.DatabaseError as e:
        print(e)
        return e
    
    if db_columns:
        return db_columns
    else:
        print("Unfortunately DB with name '{}' doesn't exist".format(db_name))    


def get_specific_cat_info_from_db(game):
    desc = game[2].split()
    desc_to_pull = desc[1] + " " + desc[2] + " " + desc[3] + " " + desc[4] + " " + desc[5]
    # desc = game.split()
    # desc_to_pull = desc[1] + " " + desc[2] + " " + desc[3] + " " + desc[4] + " " + desc[5]
    cur = conn.cursor()
    game_specific_categories = None
    query_bgg_data = """ select designer0,artist0,artist1,artist2,category0,category1,category2,category3, \
                honor0,honor1,honor2 from bgg_data where description like '%{}%'""".format(desc_to_pull)
    try:
        cur.execute(query_bgg_data)
        game_specific_categories = cur.fetchall()
    except psycopg2.DatabaseError as e:
        print(e)
        return e

    return game_specific_categories
    


# asd = get_specific_cat_info_from_db("game is a time of unrest")

# asd = get_db_column_names('big_bgg_data')
# print(asd)

# games = pull_data_for_suggested_game(['adventure','exploration'], [2,4], 60)
# for g in games:
#     print(g[1])

# close, close_under_70 = get_specific_game_from_db("sythe")
# if close:
#     print("found: ",close)
# else:
#     print("not found.", close_under_70)

