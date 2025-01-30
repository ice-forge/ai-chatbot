from app.db.memory import load_global_memory, save_global_memory

import json
import os

LOCAL_STORAGE_PATH = os.path.join(os.path.dirname(__file__), '../storage/conversations')
INDENT = 4

if not os.path.exists(LOCAL_STORAGE_PATH):
    os.makedirs(LOCAL_STORAGE_PATH)

def read_conversation_file(path):
    if (os.path.exists(path)):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                
            return {
                'name': data.get('name'),
                'conversation': data.get('conversation', []),
                'local_memory': data.get('local_memory', []),
                'attached_files': data.get('attached_files', []),
                'incoming_files': data.get('incoming_files', [])
            }
        
        except json.JSONDecodeError:
            return {
                'name': None,
                'conversation': [],
                'local_memory': [],
                'attached_files': [],
                'incoming_files': []
            }
        
    return {
        'name': None,
        'conversation': [],
        'local_memory': [],
        'attached_files': [],
        'incoming_files': []
    }

def write_conversation_file(path, data):
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=INDENT)

    except TypeError as e:
        print(f"Error writing JSON to file: {path}. Error: {e}")

def save_conversation(user_id, conversation_id, conversation = None, name = None, local_memory = None, global_memory = None, attached_files = None, incoming_files = None):
    user_folder = os.path.join(LOCAL_STORAGE_PATH, user_id)

    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    conversation_file = os.path.join(user_folder, f'{conversation_id}.json')

    existing_data = read_conversation_file(conversation_file)

    merged_data = {
        'name': name if name is not None else existing_data.get('name'),
        'conversation': conversation if conversation is not None else existing_data.get('conversation', []),
        'local_memory': local_memory if local_memory is not None else existing_data.get('local_memory', []),
        'attached_files': attached_files if attached_files is not None else existing_data.get('attached_files', []),
        'incoming_files': incoming_files if incoming_files is not None else existing_data.get('incoming_files', [])
    }

    write_conversation_file(conversation_file, merged_data)

    if global_memory is not None:
        save_global_memory(global_memory)

def get_conversation(user_id, conversation_id):
    conversation_file = os.path.join(LOCAL_STORAGE_PATH, user_id, f'{conversation_id}.json')
    data = read_conversation_file(conversation_file)

    global_memory = load_global_memory()
    data['global_memory'] = global_memory

    return data

def get_all_conversations(user_id):
    user_folder = os.path.join(LOCAL_STORAGE_PATH, user_id)
    conversations = {}

    if os.path.exists(user_folder):
        for filename in os.listdir(user_folder):
            if filename.endswith('.json'):
                conversation_id = filename[:-5]
                
                try:
                    with open(os.path.join(user_folder, filename), 'r') as f:
                        data = json.load(f)
                        conversations[conversation_id] = data

                except json.JSONDecodeError:
                    print(f"Error decoding JSON from file: {filename}, skipping this file.")

    return conversations

def delete_conversation(user_id, conversation_id):
    conversation_file = os.path.join(LOCAL_STORAGE_PATH, user_id, f'{conversation_id}.json')

    if os.path.exists(conversation_file):
        os.remove(conversation_file)

def edit_conversation_name(user_id, conversation_id, new_name):
    conversation_file = os.path.join(LOCAL_STORAGE_PATH, user_id, f'{conversation_id}.json')

    data = read_conversation_file(conversation_file)
    data['name'] = new_name

    write_conversation_file(conversation_file, data)

def get_all_saved_chats():
    all_chats = []

    for user_folder in os.listdir(LOCAL_STORAGE_PATH):
        user_path = os.path.join(LOCAL_STORAGE_PATH, user_folder)
        
        if os.path.isdir(user_path):
            for filename in os.listdir(user_path):
                if filename.endswith('.json'):
                    try:
                        with open(os.path.join(user_path, filename), 'r') as f:
                            all_chats.append(json.load(f))
                            
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON from file: {filename}, skipping this file.")
                        
    return all_chats
