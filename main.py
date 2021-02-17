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

    # if message_input == "":
    #     response = "Greetings user! I can help with any board game related "\
    #             "topic. Let me know what you desire."
    #     this_chat = Chat()
    #     this_chat.add_message("bot", response)
    # else:
    try:
        response = this_chat.add_message("human", message_input)
    except Exception as e:
        print(e)
        message = ["Sorry! There has been an issue with this chat, please "
                    "reload the page to start a new chat."]
        response = message[0]

    print("IN MAIN ",response)
    return jsonify({"message":response})
   

    # connect_db()


if __name__ == '__main__':
    app.run()


#  alias python='winpty python.exe'    <-- Messed up Microsoft duplicate, preventing python from running. Type that
