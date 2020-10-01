from flask import Flask, render_template

app = Flask(__name__, template_folder='templates')
app.config.update(
    DEBUG=True,
    TEMPLATES_AUTO_RELOAD=True
)

@app.route('/bot')
def hi():
    return render_template('index.html')

@app.route('/botmaybe', methods=["GET"])
def respond_to_user_input(self):
    checkout = print("Sending response.... ")
    return render_template('index.html', response = checkout)


@app.route('/bot', methods=["POST"])
def receive_user_input():
    # send json for object (many vars, states etc...)
    response = "Yes please!"
    print("User input received... ")
    return response

if __name__ == '__main__':
    app.run()


#  alias python='winpty python.exe'    <-- Messed up Microsoft duplicate, preventing python from running. Type that
