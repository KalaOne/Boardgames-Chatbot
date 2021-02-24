import psycopg2
from flask import Flask, render_template, request, jsonify
from bot.Chat import Chat


app = Flask(__name__, template_folder='templates')
app.config.update(
    DEBUG=True,
    TEMPLATES_AUTO_RELOAD=True
)
this_chat = None

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
    global this_chat
    this_chat = Chat()
    
    message_input = request.form['message_input']
    print("User input IN MAIN ", message_input)

    if message_input == "BOTRESPONSE" :
        message = this_chat.pop_message()
        response = message[0]
        response_required = message[1]
    else:
        try:
            response = this_chat.add_message("human", message_input)
            response_required = True
        except Exception as e:
            print(e)
            message = ["Exception: Sorry! There has been an issue with this chat, please "
                        "reload the page to start a new chat", True]
            response = message[0]
            response_required = message[1]

    print("IN MAIN ",response)
    return jsonify({"message" : response,
                    "response_required" : response_required})
   

    # connect_db()


if __name__ == '__main__':
    app.run()


#  alias python='winpty python.exe'    <-- Messed up Microsoft duplicate, preventing python from running. Type that
