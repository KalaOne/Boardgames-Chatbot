import psycopg2
from flask import Flask, render_template, request, jsonify
from bot.Chat import Chat


app = Flask(__name__, template_folder='templates')
app.config.update(
    DEBUG=True,
    TEMPLATES_AUTO_RELOAD=True
)
this_chat = Chat()

@app.route('/')
def hi():
    return render_template('index.html')

@app.route('/', methods=["POST"])
def receive_user_input():
    global this_chat
    
    message_input = request.form['message_input']
    # if message_input == "":
    #     response = "Greetings user! I can give you information about Chess. Go ahead and ask your questions. E.g. 'How to play' or 'Information'."
    #     this_chat = Chat()
    #     this_chat.add_message("bot", response)
    #     response_required = True

    if "BOTRESPONSE" in message_input:
        message = this_chat.pop_message()
        response = message['message']
        response_required = message['response_required']
    else:
        # try:
            print("Human is sending message")
            message = this_chat.add_message("human", message_input)
            response = message[0]
            response_required = message[1]
        # except Exception as e:
        #     print(e)
        #     message = ["Exception: Sorry! There has been an issue with this chat, please "
        #                 "reload the page to start a new chat", True]
        #     response = message[0]
        #     response_required = message[1]

    return jsonify({"message" : response,
                    "response_required" : response_required})
   

    # connect_db()


if __name__ == '__main__':
    app.run()


#  alias python='winpty python.exe'    <-- Messed up Microsoft duplicate, preventing python from running. Type that
