#main Flask app for Web app
from flask import Flask, redirect, render_template, url_for, request, jsonify
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
import analytics
from flask_bcrypt import Bcrypt
import os
import pandas as pd
import re
from io import StringIO
from models import db, Position
import time

app = Flask(__name__)
# Store the app startup time to invalidate old sessions
APP_START_TIME = time.time()

# Use single portfolio.db for all data
portfolio_db_uri = 'sqlite:////Users/lucaswaunn/projects/Portfolio-Analysis/backend/data/portfolio.db'
app.config['SQLALCHEMY_DATABASE_URI'] = portfolio_db_uri
app.config['SECRET_KEY'] = 'secretkey'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db.init_app(app)
Bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    # Check if session was created before app startup
    # If session_created is missing or older than app start time, invalidate session
    session_created = request.cookies.get('session_created')

    if not session_created:
        return None

    try:
        session_time = float(session_created)
        if session_time < APP_START_TIME:
            return None
    except (ValueError, TypeError):
        return None

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
    graph_html = analytics.create_DUMMY_animated_timeline_graph()
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
            response = redirect(url_for('profile'))
            # Set session_created cookie to current time for logout-on-restart functionality
            response.set_cookie('session_created', str(time.time()), max_age=2592000)  # 30 days
            return response

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

def extract_date_from_csv(content):
    """Extract date from first line of CSV file"""
    if lines := content.split('\n'):
        first_line = lines[0]
        if date_match := re.search(r'(\d{1,2}/\d{1,2}/\d{4})', first_line):
            return date_match[1]
    return "Unknown"

def process_csv_and_save_to_db(file_content):
    """Process CSV file and save to database"""
    try:
        # Extract date from first line
        date_str = extract_date_from_csv(file_content)

        # Read CSV, skipping first 3 rows
        df = pd.read_csv(StringIO(file_content), skiprows=3)

        # Drop the last column if it exists
        if len(df.columns) > 0:
            df = df.iloc[:, :-1]

        # Add date column
        df['Date'] = date_str

        # Map dataframe columns to Position model columns
        column_mapping = {
            'Symbol': 'Symbol',
            'Description': 'Description',
            'Qty (Quantity)': 'Qty_Quantity',
            'Price': 'Price',
            'Price Chng $ (Price Change $)': 'Price_Chng_Dollar',
            'Price Chng % (Price Change %)': 'Price_Chng_Percent',
            'Mkt Val (Market Value)': 'Mkt_Val',
            'Day Chng $ (Day Change $)': 'Day_Chng_Dollar',
            'Day Chng % (Day Change %)': 'Day_Chng_Percent',
            'Cost Basis': 'Cost_Basis',
            'Gain $ (Gain/Loss $)': 'Gain_Dollar',
            'Gain % (Gain/Loss %)': 'Gain_Percent',
            'Reinvest?': 'Reinvest',
            'Reinvest Capital Gains?': 'Reinvest_Capital_Gains',
            'Security Type': 'Security_Type',
            'Date': 'Date'
        }

        # Insert rows into database
        for _, row in df.iterrows():
            position = Position()
            for csv_col, db_col in column_mapping.items():
                if csv_col in row.index:
                    setattr(position, db_col, str(row[csv_col]))
            db.session.add(position)

        db.session.commit()
        return True, f"Successfully added {len(df)} positions from {date_str}"
    except Exception as e:
        db.session.rollback()
        return False, f"Error processing file: {str(e)}"

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method != 'POST':
        graph_html = analytics.create_animated_timeline_graph()
        holdings_graph_html = analytics.create_holdings_by_type_graph()
        return render_template('profile.html', graph_html=graph_html, holdings_graph_html=holdings_graph_html)
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    if file and file.filename.endswith('.csv'):
        try:
            # Read file content as string
            file_content = file.read().decode('utf-8')
            success, message = process_csv_and_save_to_db(file_content)
            if success:
                return jsonify({'success': True, 'message': message})
            else:
                return jsonify({'success': False, 'message': message}), 400
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error uploading file: {str(e)}'}), 500
    return jsonify({'success': False, 'message': 'Please upload a CSV file'}), 400

@app.route('/portfolio')
@login_required
def portfolio():
    return render_template('portfolio.html')

@app.route('/optimization')
@login_required
def optimize():
    return render_template('optimize.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)