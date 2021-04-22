import psycopg2
import psycopg2.extras
from datetime import datetime
import pandas as pd
import csv
import numpy as np


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


def get_similar_names_from_db(name):
    cur = conn.cursor()
    name0_query = "SELECT * FROM bgg_data WHERE name0_alt IS NOT NULL AND name0_alt ILIKE '{}'".format(name)
    cur.execute(name0_query)
    name0 = cur.fetchall()
    

get_similar_names_from_db("gloomhaven")