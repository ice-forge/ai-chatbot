from flask import Blueprint, render_template, redirect, url_for, jsonify, request, session
from functools import wraps

import uuid
import json

import os

from app.chat.logic import handle_send_message
from app.chat.file_processor import log_file_upload, remove_file_from_conversation

from app.db.conversation_utils import save_conversation, get_all_conversations, delete_conversation, edit_conversation_name, get_conversation
from app.db.user_utils import load_users

from app.db.memory import load_global_memory

chat = Blueprint('chat', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function

@chat.route('/get_username', methods=['GET'])
@login_required
def get_username():
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)

    username = user.get('username') if user else 'Unknown User'
    return jsonify({'username': username})

@chat.route('/chat')
@chat.route('/chat/<conversation_id>')
@login_required
def chat_page(conversation_id=None):
    users = load_users()

    user = next((u for u in users if u['id'] == session['user_id']), None)
    username = user['username'] if user and user.get('username') else 'Unknown User'
    
    return render_template('chat/chat.html', conversation_id = conversation_id, username = username)

@chat.route('/get_conversations', methods = ['GET'])
@login_required
def get_conversations():
    if request.method == 'GET':
        user_id = session['user_id']
        conversations = get_all_conversations(user_id)

        return jsonify(conversations)

@chat.route('/create_conversation', methods = ['POST'])
@login_required
def create_conversation():
    if request.method == 'POST':
        user_id = session['user_id']
        conversation_id = str(uuid.uuid4())

        save_conversation(user_id, conversation_id, [], name = "New Chat")

        return jsonify({'conversation_id': conversation_id})

@chat.route('/delete_conversation/<conversation_id>', methods = ['DELETE'])
@login_required
def delete_conversation_route(conversation_id):
    if request.method == 'DELETE':
        user_id = session['user_id']
        delete_conversation(user_id, conversation_id)
        
        return '', 204

@chat.route('/edit_conversation_name/<conversation_id>', methods = ['POST'])
@login_required
def edit_conversation_name_route(conversation_id):
    if request.method == 'POST':
        user_id = session['user_id']
        new_name = request.json.get('name')

        edit_conversation_name(user_id, conversation_id, new_name)
        
        return '', 204
    
@chat.route('/send_message', methods = ['POST'])
@login_required
def send_message():
    if request.method == 'POST':
        user_id = session['user_id']
        conversation_id = request.json.get('conversation_id')

        conversation = get_conversation(user_id, conversation_id)
        attached_files = conversation.get('attached_files', [])

        user_message = request.json.get('message')
        selected_model = request.json.get('model')
        display_files = request.json.get('files', [])

        ai_files = [{
            'name': file['filename'],
            'content': file['content'],
            'extension': file['extension']
        } for file in attached_files ]

        conversation_files = [{
            'name': file['name'],
            'color': file['color'],
            'extension': file['extension']
        } for file in display_files ]

        ai_response = handle_send_message(
            user_id = user_id, 
            conversation_id = conversation_id, 
            user_message = user_message, 
            selected_model = selected_model, 
            files = ai_files,
            display_files = conversation_files
        )
        
        return jsonify({'response': ai_response})

@chat.route('/get_memory/<conversation_id>', methods = ['GET'])
@login_required
def get_memory(conversation_id):
    if request.method == 'GET':
        user_id = session['user_id']

        global_memory = load_global_memory()
        local_memory = get_conversation(user_id, conversation_id).get('local_memory', [])

        return jsonify({
            'global_memory': global_memory,
            'local_memory': local_memory
        })

@chat.route('/upload_files', methods = ['POST'])
@login_required
def upload_files():
    if 'files' not in request.files or 'conversation_id' not in request.form:
        return jsonify({'successFiles': [], 'errors': ['No files or conversation ID provided.']})

    uploaded_files = request.files.getlist('files')
    conversation_id = request.form['conversation_id']
    user_id = session['user_id']

    successFiles = []
    errors = []

    for file in uploaded_files:
        if file.filename == '':
            errors.append('One file had no filename.')
            continue

        result = log_file_upload(file, conversation_id, user_id)

        if not result:
            errors.append(f"File not allowed or corrupted: {file.filename}")
        else:
            successFiles.append({'name': result['filename']})

    return jsonify({
        'successFiles': successFiles,
        'errors': errors,
        'message': '\n'.join(errors) if errors else None
    })

@chat.route('/remove_file', methods=['POST'])
def remove_file():
    data = request.get_json()

    filename = data.get('filename')
    conversation_id = data.get('conversation_id')
    
    if not filename or not conversation_id:
        return jsonify({'status': 'error', 'message': 'Missing required parameters'}), 400
    
    try:
        result = remove_file_from_conversation(filename, conversation_id, session.get('user_id'))
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@chat.route('/get_models', methods = ['GET'])
@login_required
def get_models():
    if request.method == 'GET':
        with open(os.path.join(os.path.dirname(__file__), '../storage/db/models.json'), 'r') as f:
            data = json.load(f)

        return jsonify({
            'models': data['models']
        })

@chat.route('/logout', methods = ['POST'])
@login_required
def logout():
    if request.method == 'POST':
        session.pop('user_id', None)
        return redirect(url_for('auth.login'))
