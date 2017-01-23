from flask_wtf import Form
from wtforms import StringField
from wtforms import PasswordField
from wtforms.validators import DataRequired

class QueryForm(Form):
	query = StringField('query', validators=[DataRequired()])

class AddForm(Form):
	add = StringField('add', validators=[DataRequired()])

class UpdateForm(Form):
	update = StringField('update', validators=[DataRequired()])

class DeleteForm(Form):
	delete = StringField('delete', validators=[DataRequired()])

class LoginForm(Form):
	username = StringField('username', validators=[DataRequired()])
	password = PasswordField('password', validators=[DataRequired()])