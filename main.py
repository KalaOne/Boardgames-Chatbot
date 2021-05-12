import psycopg2
from flask import Flask, render_template, request, jsonify
from bot.Chat import Chat
import csv


app = Flask(__name__, template_folder='templates')
app.config.update(
    DEBUG=True,
    TEMPLATES_AUTO_RELOAD=True
)
this_chat = None

@app.route('/')
def hi():
    return render_template('index.html')

@app.route('/', methods=["POST"])
def receive_user_input():
    global this_chat
    
    message_input = request.form['message_input']

    if message_input == "":
        this_chat = Chat()
        response = "Greetings user! I can give you specific information about a board game of your interest \
                or help you find a suitable game for yourself. \
                Specify a game and continue with your questions. If you want to know I can do, type 'help'."
        this_chat.add_message("bot", response)
        response_required = True
        background = False
    elif "BOTRESPONSE" in message_input:
        message = this_chat.pop_message()
        response = message['message']
        response_required = message['response_required']
        background = False
    else:
        # try:
        message = this_chat.add_message("human", message_input)
        response = message[0]
        response_required = message[1]
        background = message[2]
        # except Exception as e:
        #     print(e)
        #     message = ["Exception: Sorry! There has been an issue with this chat, please "
        #                 "reload the page to start a new chat", True]
        #     response = message[0]
        #     response_required = message[1]

    return jsonify({"message" : response,
                    "response_required" : response_required,
                    "background" : background})
   

    # connect_db()


if __name__ == '__main__':
    app.run()

#  alias python='winpty python.exe'    <-- Messed up Microsoft duplicate, preventing python from running. Type that
