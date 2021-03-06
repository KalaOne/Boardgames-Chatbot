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
        return the_game, close_game

    # clean_description = re.sub('<[^<]+?>', '', game_data[0][2])
    # print(clean_description)

    cur.close()

    return game_data, close_game



# close, close_under_70 = get_specific_game_from_db("sythe")
# if close:
#     print("found: ",close)
# else:
#     print("not found.", close_under_70)

