from flask import Blueprint, render_template, redirect, url_for, request, session
from werkzeug.security import generate_password_hash, check_password_hash

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.db.user_utils import load_users, save_users
from app.auth.smtp_utils import send_smtp_email

import uuid
from datetime import datetime, timedelta, timezone

import random

import os
from dotenv import load_dotenv

load_dotenv()

smtp_server_email = os.getenv('EMAIL')

password_reset_token_duration = 15 * 60  # 15 minutes in seconds
confirm_email_token_duration = 15 * 60  # 15 minutes in seconds

auth = Blueprint('auth', __name__)

# User class

class User:
    def __init__(self, email, password):
        self.id = str(uuid.uuid4())
        
        self.email = email
        self.password = generate_password_hash(password)
        self.username = None
        self.reset_token = None
        self.reset_token_created_at = None

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'password': self.password,
            'username': self.username,
            'reset_token': self.reset_token,
            'reset_token_created_at': self.reset_token_created_at
        }

# Helper functions

def generate_six_digit_code():
    return ''.join(str(random.randint(0, 9)) for _ in range(6))

def send_email(user_email, subject, body):
    msg = MIMEMultipart()

    msg["From"] = smtp_server_email
    msg["To"] = user_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))
    send_smtp_email(msg)

def reset_password_reset_tokens(user):
    user['reset_token'] = None
    user['reset_token_created_at'] = None

def reset_confirmation_codes():
    session.pop('confirm_code', None)
    session.pop('confirm_code_created_at', None)

def calculate_remaining_time(created_at_str, duration):
    created_at = datetime.fromisoformat(created_at_str)
    time_elapsed = datetime.now(timezone.utc) - created_at
    time_remaining = timedelta(seconds=duration) - time_elapsed
    
    if time_remaining.total_seconds() <= 0:
        return None
    
    minutes_left = int(time_remaining.total_seconds() // 60)
    seconds_left = int(time_remaining.total_seconds() % 60)
    
    return minutes_left, seconds_left

# Routes

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        users = load_users()
        user = next((u for u in users if u['email'] == email), None)

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect(url_for('chat.chat_page'))
        
        return render_template('auth/login.html', error = 'Invalid credentials or account does not exist')

@auth.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'GET':
        session.pop('pending_registration', None)
        reset_confirmation_codes()

        return render_template('auth/register.html')

    if request.method == 'POST':
        email = request.form.get('email')

        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        username = request.form.get('username')

        if password != confirm_password:
            return render_template('auth/register.html', error = 'Passwords do not match')

        users = load_users()

        if any(u['email'] == email for u in users):
            return render_template('auth/register.html', error = 'Email already registered')

        session['pending_registration'] = {
            'email': email,
            'password': password,
            'username': username
        }

        return redirect(url_for('auth.confirm_email'))

@auth.route('/forgot-password', methods = ['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('auth/forgot_password.html')

    if request.method == 'POST':
        user_email = request.form.get('email')

        users = load_users()
        user = next((u for u in users if u['email'] == user_email), None)

        if user:
            user['reset_token'] = str(uuid.uuid4())
            user['reset_token_created_at'] = datetime.now(timezone.utc).isoformat()

            save_users(users)

            try:
                reset_link = url_for('auth.reset_password', token = user['reset_token'], _external = True)
                send_email(user_email, "Password Reset Request", f"Click the link to reset your password: {reset_link}")

            except Exception as ex:
                return render_template('auth/forgot_password.html', error = ex)

            return render_template('auth/forgot_password.html', success = "A password reset link has been sent to your email successfully.")
        
        return render_template('auth/forgot_password.html', error = 'An error occured: No account found with this email.')

@auth.route('/reset-password/<token>', methods = ['GET', 'POST'])
def reset_password(token):
    users = load_users()
    user = next((u for u in users if u['reset_token'] == token), None)

    reset_token_invalid_message = "Your reset token is invalid. Please return to the forgot password page."

    if not user or not user['reset_token']:
        return render_template('auth/reset_password.html', error = reset_token_invalid_message)

    remaining_time = calculate_remaining_time(user['reset_token_created_at'], password_reset_token_duration)

    if remaining_time is None:
        reset_password_reset_tokens(user)
        save_users(users)

        return render_template('auth/reset_password.html', error = reset_token_invalid_message)

    if request.method == 'GET':
        minutes_left, seconds_left = remaining_time
        info_message = f"Token expires in {minutes_left} minutes and {seconds_left} seconds."

        return render_template('auth/reset_password.html', token = token, info = info_message)

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            return render_template('auth/reset_password.html', error = 'Passwords do not match')

        if check_password_hash(user['password'], new_password):
            return render_template('auth/reset_password.html', error = 'New password cannot be the same as the old password')

        user['password'] = generate_password_hash(new_password)

        reset_password_reset_tokens(user)
        save_users(users)

        return render_template('auth/reset_password.html', success = 'Password has been reset successfully.')

@auth.route('/confirm-email', methods=['GET', 'POST'])
def confirm_email():
    if 'pending_registration' not in session:
        return render_template('auth/confirm_email.html', error = 'No pending registration found.')

    if request.method == 'GET':
        if 'confirm_code' not in session:
            confirm_code = generate_six_digit_code()
            user_email = session['pending_registration']['email']

            try:
                session['confirm_code'] = confirm_code
                session['confirm_code_created_at'] = datetime.now(timezone.utc).isoformat()

                send_email(user_email, "Email Confirmation Code", f"Your confirmation code is: {confirm_code}")
                
            except Exception as ex:
                return render_template('auth/confirm_email.html', error = ex)
        
        created_at_str = session.get('confirm_code_created_at')
        remaining_time = calculate_remaining_time(created_at_str, confirm_email_token_duration)
        
        if remaining_time is None:
            reset_confirmation_codes()
            return render_template('auth/confirm_email.html', error = 'Your confirmation code is invalid or expired.')

        minutes_left, seconds_left = remaining_time
        info_message = f"The code expires in {minutes_left} minutes and {seconds_left} seconds."

        return render_template('auth/confirm_email.html', info = info_message)

    if request.method == 'POST':
        code_entered = request.form.get('confirmation_code')
        stored_code = session.get('confirm_code')

        created_at_str = session.get('confirm_code_created_at')

        if not stored_code or not created_at_str:
            return render_template('auth/confirm_email.html', error = 'No code found. Please reload the page.')
        
        remaining_time = calculate_remaining_time(created_at_str, confirm_email_token_duration)

        if remaining_time is None:
            reset_confirmation_codes()
            return render_template('auth/confirm_email.html', error = 'Your confirmation code has expired.')
        
        if code_entered != stored_code:
            return render_template('auth/confirm_email.html', error = 'Invalid confirmation code.')

        reg_data = session.pop('pending_registration', None)

        new_user = User(email = reg_data['email'], password = reg_data['password'])
        new_user.username = reg_data['username']
        
        users = load_users()
        users.append(new_user.to_dict())

        save_users(users)

        reset_confirmation_codes()
        session['user_id'] = new_user.id

        return redirect(url_for('chat.chat_page'))
    
@auth.route('/logout', methods = ['POST'])
def logout():
    if request.method == 'POST':
        session.pop('user_id', None)
        return redirect(url_for('auth.login'))
