from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from data import Notes
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt

app = Flask(__name__)

#MYSQL CONF
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'rarez'
app.config['MYSQL_PASSWORD'] = 'qwerty'
app.config['MYSQL_DB'] = 'dropnote'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'


mysql = MySQL(app)
Notes = Notes()

@app.route('/')
def index():
	return render_template('home.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/notes')
def notes():
	return render_template('notes.html', notes = Notes)

@app.route('/note/<string:id>/')
def note(id):
	return render_template('note.html', id=id)

class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	email = StringField('Email', [validators.Length(min=6, max=50),validators.Regexp('^[_A-Za-z0-9-\\+]+(\\.[_A-Za-z0-9-]+)*@[A-Za-z0-9-]+(\\.[A-Za-z0-9]+)*(\\.[A-Za-z]{2,})$', message="Please provide email") ])
	password = PasswordField('Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message ='Passwords do not match')
		])
	confirm = PasswordField('Confirm Password')
@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))

		#Create Cursor
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

		#Commit to DB
		mysql.connection.commit()

		#Close DB CON
		cur.close()

		flash('Congratulations! You are now registered. Please log in', 'success')

		return redirect(url_for('index'))

	return render_template('register.html', form=form)


if __name__ == '__main__':
	app.secret_key='TOPSECRETLOL'
	app.run(debug=True)