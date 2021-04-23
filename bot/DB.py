import psycopg2
import psycopg2.extras
from datetime import datetime
import pandas as pd
import csv
import numpy as np
from fuzzywuzzy import fuzz
import re



conn = psycopg2.connect(host='localhost', port=5433, user='postgres', password='postgres')

def connect_db():
    # conn = psycopg2.connect("dbname=postgres user=postgres password=postgres")
    
    cur = conn.cursor()

    # cur.execute('SELECT version()')
    # db_version = cur.fetchone()
    # print(db_version)
    cur.execute("SELECT * FROM my_games")
    games_list = cur.fetchall()
    # print(games_list)

    # for key, value in games_list:
    #     if key == 'Monopoly':
    #         print("YES !")
    #         print("Value:", value)
    cur.close()
    conn.close()
    return games_list

def add_games_to_db(all_games):
    cur = conn.cursor()
    for game in all_games:
        try:
            query = "INSERT INTO Games VALUES(%s, %s, %s, %s, %s)"
            values = (game['rank'], game['name'], game['bgg_rating'],
                game['average_rating'],game['num_voters'])
            cur.execute(query,values)
            conn.commit()
            print("added {} to DataBase".format(game['name']))
        except (Exception, psycopg2.DatabaseError) as error:
            print("Unable to add game.", error)
            

    cur.close()
    conn.close()


def add_game_codes_to_db():
    start = datetime.now()
    s_time = start.strftime("%H:%M:%S")
    print("DB adding started at :", s_time)

    cur = conn.cursor()

    df = pd.read_csv('E:/trimmedData.csv', lineterminator='\n', error_bad_lines=False)

    df_col = list(df)
    columns = ",".join(df_col)
    values = "VALUES({})".format(",".join(["%s" for _ in df_col]))
    insert = "INSERT INTO bgg_data ({}) {}".format(columns,values)
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
    cur = conn.cursor()
    all_names_query = "SELECT name0, name1, name2, name3, name4, name5, name6, name7, name8, name9 FROM bgg_data"
    cur.execute(all_names_query)
    all_names = cur.fetchall()
    for row in all_names:
        match_ratio = 0
        for name in enumerate(row):
            if fuzz.ratio(name[1].lower(), game_name.lower()) > match_ratio:
                match_ratio = fuzz.ratio(name[1].lower(), game_name.lower())
                print("Comparing {} with '{}'. Similarity ratio is : {}".format(name[1].lower(),game_name.lower(), match_ratio))
                closest_name = name
        if match_ratio >= 70:
            print(closest_name)
            break

    cur.close()       
    return closest_name   
    

def get_data_from_db_based_on_name(game_name):
    # Get all relevant information for particular game, given it's name
    # Returns: data row for game with similar name.
    selected_game = get_similar_names_from_db(game_name)
    cur = conn.cursor()
    row_data_query = "SELECT average,usersrated,minplayers,maxplayers,playingtime,minplaytime,maxplaytime, \
        yearpublished,boardgamerank,designer0,artist0,artist1,subdomain0,category0,category1,category2, \
        honor0,honor1,expansion0,expansion1,expansion2,description,thumbnail\
                  FROM bgg_data WHERE name{} = '{}'".format(selected_game[0],selected_game[1])
    cur.execute(row_data_query)
    game_data = cur.fetchall()
    print(game_data[0][21])
    # clean_description = re.sub('<[^<]+?>', '', game_data[0][21])
    print("yes")

    cur.close()

    return game_data

get_data_from_db_based_on_name("gloomhaven")