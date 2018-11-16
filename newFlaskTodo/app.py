from functools import wraps
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from flask_mysqldb import MySQL


app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'xza3363199--AIMI'
app.config['MYSQL_DB'] = 'newFlaskTodo'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MYSQL
mysql = MySQL(app)


# Create Register Class
class RegisterForm(Form):
    name = StringField('用户昵称/NickName', [validators.Length(min=1, max=50)])
    username = StringField('用户名/UserName', [validators.Length(min=4, max=25)])
    email = StringField('邮箱/Email', [validators.Length(min=6, max=50)])
    password = PasswordField('密码/Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message="Password Do Not Match.")
    ])
    confirm = PasswordField('密码确认/Confirm Password')


# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
        # Commit to DB
        mysql.connection.commit()
        # Close connection
        cur.close()
        flash('You are now registered and can log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        # Create cursor
        cur = mysql.connection.cursor()
        # Get user By username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        if result > 0:
            # GET stored hash
            data = cur.fetchone()
            password = data['password']
            # Compare the passwords
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                flash("You are now logged in.", "success")
                return redirect(url_for('dashboard'))
            else:
                error = "Password Not Match"
                return render_template('login.html', error=error)
            cur.close()
        else:
            error = "User Name Not Found"
            return render_template('login.html', error=error)
    return render_template('login.html')


# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('请先登陆！', 'danger')
            return redirect(url_for('login'))
    return wrap


# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    backlogs = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', backlogs=backlogs)
    
    else:
        return render_template('dashboard.html')
    # Close connection
    cur.close()
    return render_template('dashboard.html')


# Create Backlog Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add
@app.route('/add_backlog', methods=['GET', 'POST'])
@is_logged_in
def add_backlog():
    form = ArticleForm(request.form)
    if request.method == 'POST':
        title = form.title.data
        body = form.body.data
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))
        mysql.connection.commit()
        cur.close()
        flash("待办事项添加完成", 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_backlog.html', form=form)


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/backlogs')
@is_logged_in
def backlogs():
    # Create cursor
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    backlogs = cur.fetchall()

    if result > 0:
        return render_template('backlogs.html', backlogs=backlogs)
    else:
        flash('目前暂无待办事项， 点击用户名进行添加', 'warning')
        return render_template('backlogs.html')
    # Close connection
    cur.close()

# Check
@app.route('/backlog/<string:id>')
@is_logged_in
def backlog(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])
    backlog = cur.fetchone()
    
    return render_template('backlog.html', backlog=backlog)


# Edit
@app.route('/edit_backlog/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_backlog(id):
    # Create Cursor
    cur = mysql.connection.cursor()
    # Get backlog by id
    result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])
    backlog = cur.fetchone()
    # Get form
    form = ArticleForm(request.form)
    # Populate backlog form fields
    form.title.data = backlog['title']
    form.body.data = backlog['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id = %s", (title, body, id))
        mysql.connection.commit()
        cur.close()
        flash("待办事项更新成功", 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_backlog.html', form=form)


# Delete
@app.route('/delete_backlog/<string:id>', methods=['POST'])
@is_logged_in
def delete_backlog(id):
    # Create cursor
    cur = mysql.connection.cursor()
    # Execute
    cur.execute("DELETE FROM articles WHERE id=%s", [id])
    # Commit to DB
    mysql.connection.commit()
    #Close connection
    cur.close()
    flash("待办事项删除成功", 'success')
    return redirect(url_for('dashboard'))


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)
