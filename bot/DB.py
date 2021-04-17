import psycopg2

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
        print(game)
        print(game['rank'])
    # for game in all_games:
    #     try:
    #         query = """INSERT INTO Games VALUES(%s, %s, %s, %s, %s)"""
    #         values = (game['rank'], game['name'], game['bgg_rating'],
    #             game['average_rating'],game['num_voters'])
    #         cur.execute(query,values)
    #         print("added {} to DataBase".format(all_games['name']))
    #     except (Exception, psycopg2.DatabaseError) as error:
    #         print("Unable to add game")
    #         print(error)
        
    # conn.commit()

    cur.close()
    conn.close()
# connect_db()
