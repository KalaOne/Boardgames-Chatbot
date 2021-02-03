from flask import Flask, render_template
import psycopg2

app = Flask(__name__, template_folder='templates')
app.config.update(
    DEBUG=True,
    TEMPLATES_AUTO_RELOAD=True
)

def connect_db():
    # conn = psycopg2.connect("dbname=postgres user=postgres password=postgres")
    conn = psycopg2.connect(host='localhost', port=5432, user='postgres', password='postgres')
    cur = conn.cursor()

    cur.execute('SELECT version()')

    db_version = cur.fetchone()
    print(db_version)

    cur.close()
    conn.close()

@app.route('/')
def hi():
    return render_template('index.html')

@app.route('/', methods=["POST"])
def receive_user_input():
    # send json for object (many vars, states etc...)
    response = "Yes please!"
    print("User input received... ")
    connect_db()
    return response

if __name__ == '__main__':
    app.run()


#  alias python='winpty python.exe'    <-- Messed up Microsoft duplicate, preventing python from running. Type that
