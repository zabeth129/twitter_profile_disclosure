# -*- coding: utf-8 -*-

__author__ = 'masaru'

import sys
import yaml
import twitter_functions as twi_func

from flask import Flask, request, render_template, session, url_for, flash, redirect, g
from flask_wtf import Form

from wtforms import TextField
from wtforms.validators import Required
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask_oauth import OAuth


sys.path.append('/template')
DATABASE_CONFIG_FILE = "config/database.yml"
TWITTER_APPLICATION_CONFIG_FILE = "config/account_info.yml"

# DB set up
database_info = yaml.load(open(DATABASE_CONFIG_FILE, 'r'))
DATABASE_URI = 'mysql://{}:{}@{}/{}?charset=utf-8'.format(
    database_info["mysql"]["development"]["user"],
    database_info["mysql"]["development"]["password"],
    database_info["mysql"]["development"]['host'],
    database_info["mysql"]["development"]["database"]
)
engine = create_engine(DATABASE_URI)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

SECRET_KEY = 'development key'
DEBUG = True

# Set Twitter authentication information
application_info = yaml.load(open(TWITTER_APPLICATION_CONFIG_FILE, 'r'))
oauth = OAuth()
twitter = oauth.remote_app('twitter',
    # unless absolute urls are used to make requests, this will be added
    # before all URLs.  This is also true for request_token_url and others.
    base_url='https://api.twitter.com/1/',
    # where flask should look for new request tokens
    request_token_url='https://api.twitter.com/oauth/request_token',
    # where flask should exchange the token with the remote application
    access_token_url='https://api.twitter.com/oauth/access_token',
    # twitter knows two authorizatiom URLs.  /authorize and /authenticate.
    # they mostly work the same, but for sign on /authenticate is
    # expected because this will give the user a slightly different
    # user interface on the twitter side.
    authorize_url='https://api.twitter.com/oauth/authenticate',
    # the consumer keys from the twitter application registry.
    consumer_key='iF0A5wqzvAYnjAPazAYGCA',
    consumer_secret='zORk04dxWVqIiFxflcUSBNV9w16Cqg5oN3h4YB0PWs'
)

# setup flask
app = Flask(__name__)
app.debug = DEBUG
app.secret_key = SECRET_KEY


def init_db():
    Base.metadata.create_all(bind=engine)


class User(Base):
    """
    CREATE TABLE users (
      id int(11) NOT NULL AUTO_INCREMENT,
      screen_name varchar(255) DEFAULT NULL,
      oauth_token varchar(255) DEFAULT NULL,
      oauth_secret varchar(255) DEFAULT NULL,
      PRIMARY KEY (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
    """
    __tablename__ = 'users'
    id = Column('user_id', Integer, primary_key=True)
    screen_name = Column(String(60))
    oauth_token = Column(String(200))
    oauth_secret = Column(String(200))

    def __init__(self, screen_name):
        self.screen_name = screen_name


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])


@app.after_request
def after_request(response):
    db_session.remove()
    return response


@twitter.tokengetter
def get_twitter_token():
    """This is used by the API to look for the auth token and secret
    it should use for API calls.  During the authorization handshake
    a temporary set of token and secret is used, but afterwards this
    function has to return the token and secret.  If you don't want
    to store this in the database, consider putting it into the
    session instead.
    """
    user = g.user
    if user is not None:
        return user.oauth_token, user.oauth_secret


@app.route('/login')
def login():
    """Calling into authorize will cause the OpenID auth machinery to kick
    in.  When all worked out as expected, the remote application will
    redirect back to the callback URL provided.
    """
    return twitter.authorize(callback=url_for('oauth_authorized',
        next=request.args.get('next') or request.referrer or None))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash(u'You were signed out')
    return redirect(request.referrer or url_for('index'))


@app.route('/oauth-authorized')
@twitter.authorized_handler
def oauth_authorized(resp):
    """Called after authorization.  After this function finished handling,
    the OAuth information is removed from the session again.  When this
    happened, the tokengetter from above is used to retrieve the oauth
    token and secret.

    Because the remote application could have re-authorized the application
    it is necessary to update the values in the database.

    If the application redirected back after denying, the response passed
    to the function will be `None`.  Otherwise a dictionary with the values
    the application submitted.  Note that Twitter itself does not really
    redirect back unless the user clicks on the application name.
    """
    next_url = request.args.get('next') or url_for('index')
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    user = User.query.filter_by(name=resp['screen_name']).first()

    # user never signed on
    if user is None:
        user = User(resp['screen_name'])
        db_session.add(user)

    # in any case we update the authenciation token in the db
    # In case the user temporarily revoked access we will have
    # new tokens here.
    user.oauth_token = resp['oauth_token']
    user.oauth_secret = resp['oauth_token_secret']
    db_session.commit()

    session['user_id'] = user.id
    flash('You were signed in')
    return redirect(next_url)


class CreateForm(Form):
    screen_name = TextField(u'Twitter ID', description=u'Twitter ID', validators=[Required()])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    twitter = '@ru_pe129'
    email = 'massaru129[a]gmail.com'
    return render_template('contact.html', twitter=twitter, email=email)


@app.route('/analyze', methods=['GET', 'POST'])
def analyze_profile():
    form = CreateForm(csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        results = twi_func.disclose_profile(api=api, screen_name=form.screen_name.data)
        return render_template('results.html', results=results, screen_name=form.screen_name.data)
    return render_template('index.html', form=form)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)