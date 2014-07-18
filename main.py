# -*- coding: utf-8 -*-

__author__ = 'masaru'

import sys
import db
from twitter_functions import
from flask import Flask, request, render_template, jsonify
from flask_bootstrap import Bootstrap

sys.path.append('/template')


api = db.api
app = Flask(__name__)
Bootstrap(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register')
def register():
    pass


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    twitter = '@ru_pe129'
    email = 'massaru129[a]gmail.com'
    return render_template('contact.html', twitter=twitter, email=email)


@app.route('/twitter', methods=['GET', 'POST'])
def show_tweets():
    me = api.me()
    profiles = {}
    profiles['name'] = me.name
    profiles['image'] = me.profile_image_url
    profiles['description'] = me.description
    #profiles['back_image'] = me.profile_background_image_url
    tweets = api.home_timeline()
    return render_template('tweets.html', tweets=tweets, profiles=profiles)


@app.route('/check')
def check_func():
    me = api.me()
    profiles = {} # 情報いろいろ格納用
    profiles['name'] = me.name # プロフィールで指定した名前の取得
    profiles['image'] = me.profile_image_url # プロフィール画像のURLの取得
    profiles['description'] = me.description # 自己紹介文の取得
    tweets = api.home_timeline()
    words = []
    for i in range(0, len(tweets)):
        words.append(tweets[i].text)
    return render_template('show_tweets.html', tweets=tweets, words=words, profiles=profiles)


if __name__=="__main__":
    #app.run(host="0.0.0.0", port=80, debug=True)
    app.run(debug=True)
