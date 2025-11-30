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
from models import db, Position, UploadedFile
import time
from datetime import datetime
from catboost import CatBoostClassifier
import numpy as np

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
    return render_template('index.html')

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
    """Extract date from first line of CSV file, or use today's date if not found"""
    if lines := content.split('\n'):
        first_line = lines[0]

        # Try YYYY/MM/DD format first (2025/11/25)
        if date_match := re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', first_line):
            year, month, day = date_match.groups()
            return f'{month}/{day}/{year}'

        # Try MM/DD/YYYY format (11/25/2025)
        if date_match := re.search(r'(\d{1,2}/\d{1,2}/\d{4})', first_line):
            return date_match[1]

    # If no date found, use today's date in MM/DD/YYYY format
    today = datetime.now()
    return today.strftime('%m/%d/%Y')

def process_csv_and_save_to_db(file_content, user_id, filename):
    """Process CSV file and save to database, associated with the given user"""
    try:
        # Extract date from first line
        date_str = extract_date_from_csv(file_content)

        # Read CSV, skipping first 2 rows (title and blank line)
        # Row 3 contains the headers
        df = pd.read_csv(StringIO(file_content), skiprows=2)

        # Remove empty columns (often added by CSV format with trailing commas)
        df = df.dropna(axis=1, how='all')

        # Drop the last column if it's empty or unnamed
        if len(df.columns) > 0 and (df.columns[-1] == '' or pd.isna(df.columns[-1]) or 'Unnamed' in str(df.columns[-1])):
            df = df.iloc[:, :-1]

        # Strip whitespace from column names in case there are any
        df.columns = df.columns.str.strip()

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

        # Insert rows into database, associating each position with the user
        position_count = 0
        for _, row in df.iterrows():
            position = Position()
            position.user_id = user_id  # Link position to the current user
            for csv_col, db_col in column_mapping.items():
                if csv_col in row.index:
                    # Convert NaN/None to None for proper NULL storage
                    value = row[csv_col]
                    value = None if pd.isna(value) else str(value).strip()
                    setattr(position, db_col, value)
            db.session.add(position)
            position_count += 1

        db.session.commit()

        # Record the file upload in the uploaded_files table
        uploaded_file = UploadedFile(
            user_id=user_id,
            filename=filename,
            position_count=position_count
        )
        db.session.add(uploaded_file)
        db.session.commit()

        return True, f"Successfully added {position_count} positions from {date_str}", position_count
    except Exception as e:
        db.session.rollback()
        return False, f"Error processing file: {str(e)}", 0

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method != 'POST':
        # Fetch user's 5 most recently uploaded files
        uploaded_files = UploadedFile.query.filter_by(user_id=current_user.id).order_by(UploadedFile.upload_date.desc()).limit(5).all()

        graph_html = analytics.create_animated_timeline_graph(current_user.id)
        holdings_graph_html = analytics.create_holdings_by_type_graph(current_user.id)
        return render_template('profile.html', graph_html=graph_html, holdings_graph_html=holdings_graph_html, files=uploaded_files)
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    if file and file.filename.endswith('.csv'):
        try:
            # Read file content as string
            file_content = file.read().decode('utf-8')
            success, message, position_count = process_csv_and_save_to_db(file_content, current_user.id, file.filename)
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

@app.route('/recommendations')
@login_required
def optimize():
    # Load and prepare data
    df = pd.read_csv('../backend/stock_features.csv')
    df['date'] = pd.to_datetime(df['date'])
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    
    feature_cols = [
        'momentum', 'volatility', 'avg_correlation', 'max_correlation',
        'min_correlation', 'market_correlation', 'sharpe', 'momentum_accel',
        'dividend_yield'
    ]
    
    # Train model
    model = CatBoostClassifier(
        iterations=200,
        depth=4,
        learning_rate=0.05,
        random_state=42,
        verbose=False
    )
    model.fit(df[feature_cols], df['beat_market'])
    
    # Get latest data
    latest_date = df['date'].max()
    latest = df[df['date'] == latest_date].copy()
    latest['prob_beat_market'] = model.predict_proba(latest[feature_cols])[:, 1]
    
    # Get top recommendations
    top_picks = latest[latest['prob_beat_market'] >= 0.5].sort_values(
        'prob_beat_market', ascending=False
    ).head(20)
    
    # Convert to list of dicts for template
    recommendations = top_picks[[
        'ticker', 'prob_beat_market', 'sharpe', 'momentum', 'momentum_accel', 'volatility', 'dividend_yield', 'avg_correlation', 'market_correlation'
    ]].to_dict('records')
    
    # Summary stats
    stats = {
        'total_analyzed': len(latest),
        'above_50': len(latest[latest['prob_beat_market'] > 0.5]),
        'above_55': len(latest[latest['prob_beat_market'] > 0.55]),
        'above_60': len(latest[latest['prob_beat_market'] > 0.6]),
        'avg_prob': latest['prob_beat_market'].mean() * 100,
        'max_prob': latest['prob_beat_market'].max() * 100,
        'last_updated': latest_date.strftime('%Y-%m-%d')
    }
    
    return render_template('recommend.html', recommendations=recommendations, stats=stats)

@app.route('/delete-file/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    """Delete an uploaded file and all associated positions"""
    try:
        # Find the file to delete
        uploaded_file = UploadedFile.query.get(file_id)

        if not uploaded_file:
            return jsonify({'success': False, 'message': 'File not found'}), 404

        # Verify the file belongs to the current user (security check)
        if uploaded_file.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        # Delete all positions associated with this file
        # We can identify them by filename and user_id (positions from this upload)
        Position.query.filter_by(
            user_id=current_user.id,
            Date=uploaded_file.upload_date.strftime('%m/%d/%Y')
        ).delete()

        # Delete the file record
        db.session.delete(uploaded_file)
        db.session.commit()

        return jsonify({'success': True, 'message': 'File deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting file: {str(e)}'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)