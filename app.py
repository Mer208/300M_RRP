from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import pandas as pd
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_migrate import Migrate

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Database configuration
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Handle Render's PostgreSQL URL
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/300m_trials'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)

class Athlete(db.Model):
    __tablename__ = 'athletes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    time_trials = db.relationship('TimeTrial', backref='athlete', lazy=True)

class TimeTrial(db.Model):
    __tablename__ = 'time_trials'
    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trial_date = db.Column(db.Date, nullable=False)
    time_seconds = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
            
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/select-athletes')
@login_required
def select_athletes():
    athletes = Athlete.query.order_by(Athlete.grade, Athlete.name).all()
    return render_template('select_athletes.html', athletes=athletes, single=True)

@app.route('/select-group-athletes')
@login_required
def select_group_athletes():
    athletes = Athlete.query.order_by(Athlete.grade, Athlete.name).all()
    return render_template('select_athletes.html', athletes=athletes, single=False)

@app.route('/record-time', methods=['GET', 'POST'])
@login_required
def record_time():
    if request.method == 'POST':
        athlete_ids = request.form.getlist('athlete_ids[]')
        if not athlete_ids:
            flash('Please select at least one athlete', 'error')
            return redirect(url_for('select_athletes'))
        
        if len(athlete_ids) > 1:
            flash('Please select only one athlete for individual time recording', 'error')
            return redirect(url_for('select_athletes'))
        
        athlete = Athlete.query.get(athlete_ids[0])
        return render_template('record_time.html', athlete=athlete)
    
    return redirect(url_for('select_athletes'))

@app.route('/record-group-time', methods=['GET', 'POST'])
@login_required
def record_group_time():
    if request.method == 'POST':
        athlete_ids = request.form.getlist('athlete_ids[]')
        if not athlete_ids:
            flash('Please select at least one athlete', 'error')
            return redirect(url_for('select_group_athletes'))
        
        athletes = Athlete.query.filter(Athlete.id.in_(athlete_ids)).order_by(Athlete.grade, Athlete.name).all()
        return render_template('record_group_time.html', athletes=athletes)
    
    return redirect(url_for('select_group_athletes'))

@app.route('/rankings')
def rankings():
    grade = request.args.get('grade', type=int)
    time_frame = request.args.get('time_frame', 'all')
    
    # Base query for rankings
    query = db.session.query(
        Athlete.name,
        Athlete.grade,
        TimeTrial.time_seconds,
        TimeTrial.trial_date,
        User.username.label('coach_username')
    ).select_from(TimeTrial).join(
        Athlete, TimeTrial.athlete_id == Athlete.id
    ).join(
        User, TimeTrial.coach_id == User.id
    )
    
    if grade:
        query = query.filter(Athlete.grade == grade)
    
    if time_frame == 'week':
        week_ago = datetime.now() - timedelta(days=7)
        query = query.filter(TimeTrial.trial_date >= week_ago)
    elif time_frame == 'season':
        season_start = datetime(datetime.now().year, 8, 1)  # Assuming season starts in August
        query = query.filter(TimeTrial.trial_date >= season_start)
    
    rankings = query.order_by(TimeTrial.time_seconds).all()

    # Get grade distribution data
    grade_distribution = db.session.query(
        Athlete.grade,
        db.func.count(db.distinct(Athlete.id)).label('count')
    ).group_by(Athlete.grade).order_by(Athlete.grade).all()

    # Get time trends data (average times per week)
    time_trends = db.session.query(
        db.func.date_trunc('week', TimeTrial.trial_date).label('week'),
        db.func.avg(TimeTrial.time_seconds).label('avg_time')
    ).group_by('week').order_by('week').limit(4).all()

    return render_template('rankings.html', 
                         rankings=rankings, 
                         enumerate=enumerate,
                         grade_distribution=grade_distribution,
                         time_trends=time_trends)

@app.route('/most_improved')
def most_improved():
    # Query to get most improved athletes by comparing their first and last times
    improved = db.session.query(
        Athlete.name,
        Athlete.grade,
        db.func.min(TimeTrial.time_seconds).label('first_time'),
        db.func.max(TimeTrial.time_seconds).label('last_time'),
        (db.func.max(TimeTrial.time_seconds) - db.func.min(TimeTrial.time_seconds)).label('improvement')
    ).join(TimeTrial).group_by(
        Athlete.id,
        Athlete.name,
        Athlete.grade
    ).having(
        db.func.count(TimeTrial.id) > 1  # Only include athletes with multiple trials
    ).order_by(
        db.desc('improvement')  # Order by largest improvement first
    ).limit(10).all()
    
    return render_template('most_improved.html', improved=improved, enumerate=enumerate)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.')
    return redirect(url_for('index'))

@app.route('/import_athletes', methods=['GET', 'POST'])
@login_required
def import_athletes():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
            
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            flash('Invalid file format. Please upload a CSV or Excel file')
            return redirect(request.url)
            
        try:
            # Read the file
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
                
            # Validate required columns
            required_columns = ['firstname', 'lastname', 'grade']
            if not all(col in df.columns for col in required_columns):
                flash('File must contain columns: firstname, lastname, grade')
                return redirect(request.url)
                
            # Process each row
            imported_count = 0
            skipped_count = 0
            for _, row in df.iterrows():
                try:
                    # Clean and validate data
                    firstname = str(row['firstname']).strip()
                    lastname = str(row['lastname']).strip()
                    grade = int(row['grade'])
                    
                    if not firstname or not lastname or grade not in [9, 10, 11, 12]:
                        skipped_count += 1
                        continue
                        
                    full_name = f"{firstname} {lastname}"
                    
                    # Check if athlete already exists
                    athlete = Athlete.query.filter_by(
                        name=full_name,
                        grade=grade
                    ).first()
                    
                    if not athlete:
                        athlete = Athlete(
                            name=full_name,
                            grade=grade
                        )
                        db.session.add(athlete)
                        imported_count += 1
                except (ValueError, TypeError):
                    skipped_count += 1
                    continue
            
            db.session.commit()
            flash(f'Successfully imported {imported_count} athletes. Skipped {skipped_count} invalid entries.')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'Error importing athletes: {str(e)}')
            return redirect(request.url)
            
    return render_template('import_athletes.html')

def send_reset_email(user_email, reset_url):
    msg = MIMEMultipart()
    msg['From'] = app.config['MAIL_USERNAME']
    msg['To'] = user_email
    msg['Subject'] = "Password Reset Request"
    
    body = f"""
    Hello,
    
    You have requested to reset your password. Please click the link below to reset your password:
    
    {reset_url}
    
    If you did not request this password reset, please ignore this email.
    
    This link will expire in 1 hour.
    
    Best regards,
    300M Trials Team
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            # Create reset URL
            reset_url = url_for('reset_password', token=token, _external=True)
            
            # Send reset email
            if send_reset_email(user.email, reset_url):
                flash('Password reset instructions have been sent to your email.', 'success')
            else:
                flash('Error sending reset email. Please try again.', 'error')
        else:
            # Don't reveal that the email doesn't exist
            flash('If an account exists with that email, you will receive password reset instructions.', 'info')
            
        return redirect(url_for('login'))
        
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or user.reset_token_expiry < datetime.utcnow():
        flash('Invalid or expired password reset link.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
        
        user.password_hash = generate_password_hash(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        flash('Your password has been reset successfully.', 'success')
        return redirect(url_for('login'))
        
    return render_template('reset_password.html', token=token)

if __name__ == '__main__':
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Check if we need to create the migrations directory
        if not os.path.exists('migrations'):
            print("Initializing database migrations...")
            os.system('flask db init')
        
        # Create and apply migrations
        print("Creating database migrations...")
        os.system('flask db migrate -m "Initial migration"')
        print("Applying database migrations...")
        os.system('flask db upgrade')
    
    # Use environment variable for port in production
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 
