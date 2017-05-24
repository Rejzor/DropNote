from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
app = Flask(__name__)

#MYSQL CONF
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'rarez'
app.config['MYSQL_PASSWORD'] = 'qwerty'
app.config['MYSQL_DB'] = 'dropnote'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'


mysql = MySQL(app)

@app.route('/')
def index():
	return render_template('home.html')

@app.route('/about')
def about():
	return render_template('about.html')

#Check if user logged in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, Please login', 'danger')
			return redirect(url_for('login'))

	return wrap

@app.route('/notes')
@is_logged_in
def notes():
	#CREATE CURSOR
	cur = mysql.connection.cursor()

	#GET NOTES
	result = cur.execute('SELECT * FROM notes')
	notes = cur.fetchall()
	if result > 0:
		return render_template('notes.html', notes=notes)
	else:
		 message = "No notes found"
		 render_template('notes.html', message=message)
	#CLOSE CONNECTION
	cur.close()

#SINGLE NOTE
@app.route('/note/<string:id>/')
@is_logged_in
def note(id):
		#CREATE CURSOR
	cur = mysql.connection.cursor()

	#GET NOTES
	result = cur.execute('SELECT * FROM notes WHERE id = %s', [id])
	note = cur.fetchone()
	return render_template('note.html', note=note)
#REGISTER FORM CLASS
class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	email = StringField('Email', [validators.Length(min=6, max=50),validators.Regexp('^[_A-Za-z0-9-\\+]+(\\.[_A-Za-z0-9-]+)*@[A-Za-z0-9-]+(\\.[A-Za-z0-9]+)*(\\.[A-Za-z]{2,})$', message="Please provide email") ])
	password = PasswordField('Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message ='Passwords do not match')
		])
	confirm = PasswordField('Confirm Password')
#REGISTER
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
#USER LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
	#GET FORM FIELDS
		username = request.form['username']
		password_candidate = request.form['password']

		#CREATE DB CURSOR
		cur = mysql.connection.cursor()

		#GET USER BY USERNAME
		result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

		if result > 0:
			#GET STORED HASH
			data = cur.fetchone()
			password = data['password']

			#COMPARE PASSWORD

			if sha256_crypt.verify(password_candidate, password):
				app.logger.info('PASSWORD CORRECT')
				session['logged_in'] = True
				session['username'] = username

				flash('You are now logged in', 'success')
				return redirect(url_for('dashboard'))
			else:
				app.logger.info('BAD PASSWORD')
				error = 'Invalid login'
				return render_template('login.html', error=error)
			cur.close()
		else:
			app.logger.info('NO USER')
			error = 'User not found'
			return render_template('login.html', error=error)

	return render_template('login.html')


#LOGOUT
@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are now logged out', 'success')
	return redirect(url_for('login'))

#DASHBOARD
@app.route('/dashboard')
@is_logged_in
def dashboard():
	#CREATE CURSOR
	cur = mysql.connection.cursor()

	#GET NOTES
	result = cur.execute('SELECT * FROM notes')
	notes = cur.fetchall()
	if result > 0:
		return render_template('dashboard.html', notes=notes)
	else:
		 message = "No notes found"
		 render_template('dashboard.html', message=message)

	return render_template('dashboard.html')
	#CLOSE CONNECTION
	cur.close()

#NOTE FORM CLASS
class NoteForm(Form):
	title = TextAreaField('Title', [validators.Length(min=1, max=500)])
	body= TextAreaField('Body', [validators.Length(min=5)])


#ADD NOTE
@app.route('/add_note', methods=['GET','POST'])
@is_logged_in
def add_note():
	form = NoteForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data

		#CREATE DB CURSOR
		cur = mysql.connection.cursor()
		#EXECUTE
		cur.execute('INSERT INTO notes(title, body, author) VALUES(%s, %s, %s)',(title, body, session['username']))

		#COMMIT TO DB
		mysql.connection.commit()
		#CLOSE CONNECTION
		cur.close()
		flash('Note Created', 'success')

		return redirect(url_for('dashboard'))
	return render_template('add_note.html', form=form)

#EDIT NOTE
@app.route('/edit_note/<string:id>', methods=['GET','POST'])
@is_logged_in
def edit_note(id):
	#Create cursor
	cur = mysql.connection.cursor()

	#GET NOTE by id
	result = cur.execute("SELECT * FROM notes WHERE id = %s", [id])
	note = cur.fetchone()
	#GET FORM
	form = NoteForm(request.form)
	#POPULATE NOTE FIELDS
	form.title.data = note['title']
	form.body.data = note['body']


	if request.method == 'POST' and form.validate():
		title = request.form['title']
		body = request.form['body']
		#CREATE DB CURSOR
		cur = mysql.connection.cursor()
		#EXECUTE
		cur.execute('UPDATE notes SET title=%s, body=%s WHERE id = %s', (title, body, id) )

		#COMMIT TO DB
		mysql.connection.commit()
		#CLOSE CONNECTION
		cur.close()
		flash('Note Updated', 'success')

		return redirect(url_for('dashboard'))
	return render_template('edit_note.html', form=form)
@app.route('/delete_note/<string:id>', methods=['POST'])
@is_logged_in
def delete_note(id):
	#Create cursor
	cur = mysql.connection.cursor()
	#GET NOTE by id
	cur.execute("DELETE FROM notes WHERE id = %s", [id])
	#COMMIT TO DB
	mysql.connection.commit()
	#CLOSE CONNECTION
	cur.close()

	flash('Note Deleted', 'success')

	return redirect(url_for('dashboard'))

if __name__ == '__main__':
	app.secret_key='TOPSECRETLOL'
	app.run(debug=True)