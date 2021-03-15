import psycopg2

def connect_db():
    # conn = psycopg2.connect("dbname=postgres user=postgres password=postgres")
    conn = psycopg2.connect(host='localhost', port=5433, user='postgres', password='postgres')
    cur = conn.cursor()

    # cur.execute('SELECT version()')
    # db_version = cur.fetchone()
    # print(db_version)
    cur.execute("SELECT * FROM Games")
    games_list = cur.fetchall()
    # print(games_list)
    print(type(games_list))
    for key, value in games_list:
        if key == 'Monopoly':
            print("YES !")
            print("Value:", value)
    cur.close()
    conn.close()

connect_db()
