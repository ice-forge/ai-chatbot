
from flask import Blueprint, redirect, url_for, session

main = Blueprint('main', __name__)

@main.route('/', methods = ['GET', 'POST'])
def home():
    if 'user_id' in session:
        return redirect(url_for('chat.chat_page'))
    
    return redirect(url_for('auth.login'))
