from web import app
from flask import render_template
from flask_wtf import FlaskForm

from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, InputRequired

import sys


class NameForm(FlaskForm):
    name = StringField('你的名字?', validators=[DataRequired()])
    submit = SubmitField('提交')


@app.route('/', methods=['GET', 'POST'])
def index():
    name = None
    name_form = NameForm()

    if name_form.validate_on_submit():
        name = name_form.name.data
        name_form.name.data = ''

    return render_template('index.html', form=name_form, name=name)