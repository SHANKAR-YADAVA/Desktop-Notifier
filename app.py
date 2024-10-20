from flask import Flask, redirect, render_template, request, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from plyer import notification
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import secrets

secret_key = secrets.token_hex(16)

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///../instance/todo.db"  # Ensure this path is correct
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = secret_key

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    todos = db.relationship('Todo', backref='user', lazy=True)

# Todo model
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    notify_time = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # No hashing, plain text comparison
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, password=password)  # Password stored as plain text
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('Registration successful.', 'success')
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        notify_time = request.form.get('notify_time')
        notify_time = datetime.strptime(notify_time, '%Y-%m-%dT%H:%M') if notify_time else None
        todo = Todo(title=title, desc=desc, notify_time=notify_time, user_id=current_user.id)
        db.session.add(todo)
        db.session.commit()

    allTodo = Todo.query.filter_by(user_id=current_user.id).all()
    return render_template('home.html', allTodo=allTodo)

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    todo = Todo.query.get_or_404(id)
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        notify_time = request.form.get('notify_time')
        notify_time = datetime.strptime(notify_time, '%Y-%m-%dT%H:%M') if notify_time else None
        todo.title = title
        todo.desc = desc
        todo.notify_time = notify_time
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('update.html', todo=todo)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    todo = Todo.query.get_or_404(id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('home'))

def test_notify():
    with app.app_context():
        now = datetime.now()
        todos = Todo.query.filter(Todo.notify_time <= now).all()
        for todo in todos:
            notification.notify(
                title=f"Task: {todo.title}",
                message=f"Description: {todo.desc}",
                timeout=10
            )

scheduler = BackgroundScheduler()
scheduler.add_job(test_notify, 'interval', minutes=1)
scheduler.start()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create tables if they do not exist
    app.run(debug=True)
