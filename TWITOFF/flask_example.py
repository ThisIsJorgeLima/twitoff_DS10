from flask import Flask

app = Flask(__name__)


@app.route('/')
def home():
    return "<h1>Hello, World!</h1>"


@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return f'{username}'


if __name__ == "__main__":
    app.run(debug=True, port=8080)
