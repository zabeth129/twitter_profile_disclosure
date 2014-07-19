# -*- coding: utf-8 -*-

__author__ = 'masaru'

import sys
# import db
import twitter_functions as twi_func
from flask import Flask, request, render_template, flash
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from wtforms import TextField, IntegerField, FloatField
from wtforms.validators import Required


sys.path.append('/template')


api = twi_func.authentication()
app = Flask(__name__)
Bootstrap(app)


class CreateForm(Form):
    screen_name = TextField(u'Twitter ID', description=u'Twitter ID', validators=[Required()])


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    twitter = '@ru_pe129'
    email = 'massaru129[a]gmail.com'
    return render_template('contact.html', twitter=twitter, email=email)


@app.route('/', methods=['GET', 'POST'])
def analyze_profile():
    form = CreateForm(csrf_enabled=False)
    if request.method == 'GET':
        return render_template('index.html', form=form)
    results = twi_func.disclose_profile(api=api, screen_name=form.screen_name.data)
    return render_template('results.html', results=results, screen_name=form.screen_name.data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)