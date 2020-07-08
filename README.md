# twitoff

Data Flows
The "Twitoff App" data flows are like:

The user provides an example of tweet text and selects two Twitter users to compare, which is more likely to say the example tweet text.
App requests user and tweet information from the Twitter API, as necessary, to gather data about each user, and stores it in the database.
For each tweet, the app requests Basilica API to get corresponding natural language processing embeddings and stores them in the database.
App uses the tweet embeddings from both users to train a binary classifier model.
The app makes a request to Basilica API for the natural language processing embeddings for the example tweet text. It passes those to the model as an input value to make predictions.
The app displays prediction results to the user.

# Table of contents
====================

<!--ts-->
   * [Setup](#setup)
   * [Installing package dependencies:](#installing-package-dependencies:)
   * [The Basilica API:](#the-Basilica-API:)
   * [The Twitter API and Tweepy Package:](#the-twitter-api-and-tweepy-package:)
   * [Saving tweets and users in the database.](#saving-tweets-and-users-in-the-database.)
   * [Twitter Service:](#twitter-service:)
<!--te-->

## Setup
=========
Setup and activate a virtual environment:

```sh
pipenv install
pipenv shell
```

Create a new repo on GitHub, then get it setup locally:

```sh
git clone YOUR_REMOTE_ADDRESS
cd your-repo-name
pipenv --python 3.7
```

Installing package dependencies:
================================

```sh
pipenv install Flask Flask-SQLAlchemy Flask-Migrate
```

> sign up for Basilica and Twitter API accounts, respectively:
>  + https://developer.twitter.com/en/docs
>  + https://www.basilica.ai/

Agenda:

  1. Integrating with an example API (bonus)
  2. Integrating with the Twitter API
  3. Integrating with the Basilica API
  4. Storing API data in the database

Installing package dependencies:

```sh
pipenv install python-dotenv requests basilica tweepy
```

Example ".env" file:

```sh
# .env
ALPHAVANTAGE_API_KEY="abc123"

BASILICA_API_KEY="_______________________"

TWITTER_API_KEY="_______________________"
TWITTER_API_SECRET="_______________________"
TWITTER_ACCESS_TOKEN="_______________________"
TWITTER_ACCESS_TOKEN_SECRET="_______________________"
```

> IMPORTANT: remember to add a `.env` entry into the ".gitignore" file, to prevent secret creds from being tracked in version control!!
Setup the database:


The Basilica API:
=================

  + https://www.basilica.ai/quickstart/python/
  + https://www.basilica.ai/api-keys/
  + https://basilica-client.readthedocs.io/en/latest/basilica.html

```py
# web_app/services/basilica_service.py

import basilica
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BASILICA_API_KEY")

def basilica_api_client():
    connection = basilica.Connection(API_KEY)
    print(type(connection)) #> <class 'basilica.Connection'>
    return connection

if __name__ == "__main__":

    print("---------")
    connection = basilica_api_client()

    print("---------")
    sentence = "Hello again"
    sent_embeddings = connection.embed_sentence(sentence)
    print(list(sent_embeddings))

    print("---------")
    sentences = ["Hello world!", "How are you?"]
    print(sentences)
    # it is more efficient to make a single request for all sentences...
    embeddings = connection.embed_sentences(sentences)
    print("EMBEDDINGS...")
    print(type(embeddings))
    print(list(embeddings)) # [[0.8556405305862427, ...], ...]

```

The Twitter API and Tweepy Package:
==================================

  + https://developer.twitter.com/en/docs
  + https://github.com/tweepy/tweepy
  + http://docs.tweepy.org/en/latest/
  + http://docs.tweepy.org/en/latest/api.html#API.get_user
  + http://docs.tweepy.org/en/latest/api.html#API.user_timeline

Twitter Service:
=================

```py
# web_app/services/twitter_service.py

import tweepy
import os
from dotenv import load_dotenv

load_dotenv()

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

def twitter_api():
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
    print("AUTH", auth)
    api = tweepy.API(auth)
    print("API", api)
    #print(dir(api))
    return api

if __name__ == "__main__":

    api = twitter_api()
    user = api.get_user("elonmusk")
    print("USER", user)
    print(user.screen_name)
    print(user.name)
    print(user.followers_count)

    #breakpoint()

    #public_tweets = api.home_timeline()
    #
    #for tweet in public_tweets:
    #    print(type(tweet)) #> <class 'tweepy.models.Status'>
    #    #print(dir(tweet))
    #    print(tweet.text)
    #    print("-------------")
```

Saving tweets and users in the database.
=========================================


Twitter Routes (Iteration 1, returning the results as JSON):

```py
# web_app/routes/twitter_routes.py

from flask import Blueprint, render_template, jsonify
from web_app.services.twitter_service import twitter_api_client

twitter_routes = Blueprint("twitter_routes", __name__)

@twitter_routes.route("/users/<screen_name>")
def get_user(screen_name=None):
    print(screen_name)
    api = twitter_api_client()
    user = api.get_user(screen_name)
    statuses = api.user_timeline(screen_name, tweet_mode="extended", count=150, exclude_replies=True, include_rts=False)
    return jsonify({"user": user._json, "tweets": [s._json for s in statuses]})

```

Twitter Routes (Iteration 2, storing users in the database, first need to implement the respective [`User` and `Tweet` model classes](/reference_code/models.py)):

```py
# web_app/routes/twitter_routes.py

from flask import Blueprint, render_template, jsonify
from web_app.models import db, User, Tweet, parse_records
from web_app.services.twitter_service import twitter_api_client
from web_app.services.basilica_service import basilica_api_client

twitter_routes = Blueprint("twitter_routes", __name__)

@twitter_routes.route("/users/<screen_name>")
def get_user(screen_name=None):
    print(screen_name)

    api = twitter_api_client()

    twitter_user = api.get_user(screen_name)
    statuses = api.user_timeline(screen_name, tweet_mode="extended", count=150, exclude_replies=True, include_rts=False)
    print("STATUSES COUNT:", len(statuses))
    #return jsonify({"user": user._json, "tweets": [s._json for s in statuses]})

    # get existing user from the db or initialize a new one:
    db_user = User.query.get(twitter_user.id) or User(id=twitter_user.id)
    db_user.screen_name = twitter_user.screen_name
    db_user.name = twitter_user.name
    db_user.location = twitter_user.location
    db_user.followers_count = twitter_user.followers_count
    db.session.add(db_user)
    db.session.commit()
    #breakpoint()
    return "OK"
    #return render_template("user.html", user=db_user, tweets=statuses) # tweets=db_tweets
```


Twitter Routes (Iteration 3, storing users and tweets and embeddings in the database):

```py
# web_app/routes/twitter_routes.py

from flask import Blueprint, render_template, jsonify
from web_app.models import db, User, Tweet, parse_records
from web_app.services.twitter_service import twitter_api_client
from web_app.services.basilica_service import basilica_api_client

twitter_routes = Blueprint("twitter_routes", __name__)

@twitter_routes.route("/users/<screen_name>")
def get_user(screen_name=None):
    print(screen_name)

    api = twitter_api_client()

    twitter_user = api.get_user(screen_name)
    statuses = api.user_timeline(screen_name, tweet_mode="extended", count=150, exclude_replies=True, include_rts=False)
    print("STATUSES COUNT:", len(statuses))
    #return jsonify({"user": user._json, "tweets": [s._json for s in statuses]})

    # get existing user from the db or initialize a new one:
    db_user = User.query.get(twitter_user.id) or User(id=twitter_user.id)
    db_user.screen_name = twitter_user.screen_name
    db_user.name = twitter_user.name
    db_user.location = twitter_user.location
    db_user.followers_count = twitter_user.followers_count
    db.session.add(db_user)
    db.session.commit()
    #return "OK"
    #breakpoint()

    basilica_api = basilica_api_client()

    all_tweet_texts = [status.full_text for status in statuses]
    embeddings = list(basilica_api.embed_sentences(all_tweet_texts, model="twitter"))
    print("NUMBER OF EMBEDDINGS", len(embeddings))

    # TODO: explore using the zip() function maybe...
    counter = 0
    for status in statuses:
        print(status.full_text)
        print("----")
        #print(dir(status))
        # get existing tweet from the db or initialize a new one:
        db_tweet = Tweet.query.get(status.id) or Tweet(id=status.id)
        db_tweet.user_id = status.author.id # or db_user.id
        db_tweet.full_text = status.full_text
        #embedding = basilica_client.embed_sentence(status.full_text, model="twitter") # todo: prefer to make a single request to basilica with all the tweet texts, instead of a request per tweet
        embedding = embeddings[counter]
        print(len(embedding))
        db_tweet.embedding = embedding
        db.session.add(db_tweet)
        counter+=1
    db.session.commit()
    #breakpoint()
    return "OK"
    #return render_template("user.html", user=db_user, tweets=statuses) # tweets=db_tweets
```


```html
<!-- web_app/templates/user.html -->

{% extends "layout.html" %}

{% block content %}
    <h2>Twitter User: {{ user.screen_name }} </h2>

    <p>Name: {{ user.name }}</p>
    <p>Location: {{ user.location }}</p>
    <p>Followers: {{ user.followers_count }}</p>

    {% if tweets %}
        <ul>
        {% for status in tweets %}
            <li>{{ status.full_text }}</li>
        {% endfor %}
        </ul>

    {% else %}
        <p>No tweets found.</p>
    {% endif %}

{% endblock %}
```


```sh
# Windows users can omit the "FLASK_APP=web_app" part...

FLASK_APP=web_app flask db init #> generates app/migrations dir

# run both when changing the schema:
FLASK_APP=web_app flask db migrate #> creates the db (with "alembic_version" table)
FLASK_APP=web_app flask db upgrade #> creates the specified tables
```

## Usage

Run the web app:

```sh
FLASK_APP=web_app flask run
```


  1. HTTP, Client-server architecture; Web Application Routing
  2. Web Application Views and View Templates
  3. Adding a database w/ Flask SQL Alchemy

Flask Basics:

  + https://github.com/pallets/flask
  + https://palletsprojects.com/p/flask/
  + https://flask.palletsprojects.com/en/1.1.x/quickstart/
  + https://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/
  + https://flask.palletsprojects.com/en/1.1.x/blueprints/
  + https://flask.palletsprojects.com/en/1.1.x/tutorial/static/


Testing a Flask App (FYI / BONUS):

  + https://flask.palletsprojects.com/en/1.1.x/testing/
  
Defining a basic Flask App:

```py
# hello.py

from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    x = 2 + 2
    return f"Hello World! {x}"

@app.route("/about")
def about():
    return "About me"
```

Running a Flask App:

```sh
# Mac:
FLASK_APP=hello.py flask run

# Windows:
export FLASK_APP=hello.py # one-time thing, to set the env var
flask run
```

> NOTE: if you're on Windows and `export` doesn't work for you, try `set` instead.

> NOTE: right now our app is located in the "hello.py" file, which is why we use `FLASK_APP=hello.py` but we will soon be changing this when our app grows larger...

Init file in "web_app" directory:

```py
# web_app/__init__.py

from flask import Flask

from web_app.routes.home_routes import home_routes
from web_app.routes.book_routes import book_routes

def create_app():
    app = Flask(__name__)
    app.register_blueprint(home_routes)
    app.register_blueprint(book_routes)
    return app

if __name__ == "__main__":
    my_app = create_app()
    my_app.run(debug=True)
```

Home routes:

```py
# web_app/routes/home_routes.py

from flask import Blueprint

home_routes = Blueprint("home_routes", __name__)

@home_routes.route("/")
def index():
    x = 2 + 2
    return f"Hello World! {x}"

@home_routes.route("/about")
def about():
    return "About me"
```

Running the Flask App, after new "web_app" organizational structure in place:

```sh
# Mac:
FLASK_APP=web_app flask run

# Windows:
set FLASK_APP=web_app # one-time thing, to set the env var
flask run
```


## Part VI

> FYI: As a basic requirement for this part of class, we'll just return some plain HTML pages. Only if you have time and interest should you also concern yourself with the shared layouts and the Twitter Bootstrap styling. We might have some time to review them in-class during class 4, otherwise all the info and starter code you need is below. 

HTML:
  + https://www.w3schools.com/html/html_basic.asp
  + https://www.w3schools.com/html/html_forms.asp
  
Flask View Templates:
  + https://flask.palletsprojects.com/en/1.1.x/tutorial/templates/
  + https://jinja.palletsprojects.com/en/2.11.x/templates/
  + https://jinja.palletsprojects.com/en/2.11.x/tricks/

Twitter Bootstrap:
  + https://getbootstrap.com/
  + https://getbootstrap.com/docs/4.4/getting-started/introduction/
  + https://getbootstrap.com/docs/4.0/components/navbar/
  + https://getbootstrap.com/docs/3.4/examples/navbar-fixed-top/
  + https://getbootstrap.com/docs/4.0/components/navbar/#color-schemes
  + https://stackoverflow.com/questions/19733447/bootstrap-navbar-with-left-center-or-right-aligned-items
  
  
## Part VII

Flask-SQLAlchemy:
  + https://github.com/pallets/flask-sqlalchemy/
  + https://flask-sqlalchemy.palletsprojects.com/en/2.x/
  + https://flask-sqlalchemy.palletsprojects.com/en/2.x/api/#models
  + https://docs.sqlalchemy.org/en/13/core/type_basics.html
  + https://docs.sqlalchemy.org/en/13/orm/join_conditions.html?highlight=foreign%20key

Flask-Migrate:
  + https://flask-migrate.readthedocs.io/en/latest/
  
- **[MIT license](http://opensource.org/licenses/mit-license.php)**
- Copyright 2019-2020 © <a href="http://thisisjorgelima.com" target="_blank">Jorge A. Lima</a>.
 
