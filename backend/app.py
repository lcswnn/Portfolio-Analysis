#main Flask app for Web app
from flask import Flask, redirect, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
import analytics
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/lucaswaunn/projects/Portfolio-Analysis/backend/data/account-info.db'
app.config['SECRET_KEY'] = 'secretkey'
db = SQLAlchemy(app)
Bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(30), nullable=False)
    lastname = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False) #80 not 20 since hashed passwords are longer
    
class RegisterForm(FlaskForm):
    firstname = StringField(validators=[InputRequired(), Length(
        min=2, max=30)], render_kw={"placeholder": "First Name"})
    lastname = StringField(validators=[InputRequired(), Length(
        min=2, max=30)], render_kw={"placeholder": "Last Name"})
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"})
    email = StringField(validators=[InputRequired(), Length(
        min=6, max=50)], render_kw={"placeholder": "Email"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")
    
    def validate_username(self, username):
        if existing_user_username := User.query.filter_by(
            username=username.data
        ).first():
            raise ValidationError(
                "That username already exists. Please choose a different one.")
            
            
class LogInForm(FlaskForm):
    username = StringField(validators=[InputRequired()], render_kw={"placeholder": "Username or Email"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Log In")


@app.route('/')
def index():
    # Generate the animated timeline graph
    graph_html = analytics.create_animated_timeline_graph()
    return render_template('index.html', graph_html=graph_html)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LogInForm()

    if form.validate_on_submit():
        # Check if input is email or username
        user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.username.data)
        ).first()
        if user and Bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('profile'))

    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        hashed_password = Bcrypt.generate_password_hash(form.password.data)
        new_user = User(
            firstname=form.firstname.data,
            lastname=form.lastname.data,
            email=form.email.data,
            username=form.username.data,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    return render_template('profile.html')

@app.route('/portfolio')
@login_required
def portfolio():
    return "Portfolio Page - Under Construction"

@app.route('/optimization')
@login_required
def optimize():
    return "Optimization Page - Under Construction"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)