from flask import Flask, render_template

app = Flask(__name__, template_folder='templates')
app.config.update(
    DEBUG=True,
    TEMPLATES_AUTO_RELOAD=True
)

@app.route('/bot')
def hi():
    return render_template('index.html')

@app.route('/bot', methods=["GET"])
def respond_to_user_input():
    checkout = print("Sending response.... ")
    return render_template('index.html', response = checkout)


@app.route('/bot', methods=["POST"])
def receive_user_input(user_inp):
    print("User input received... " + user_inp)
    return render_template('index.html')



if __name__ == '__main__':
    app.run()