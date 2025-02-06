from werkzeug.utils import secure_filename
from app.db.conversation_utils import get_conversation, save_conversation

ALLOWED_EXTENSIONS = {'pdf', 'txt'}

def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_file_content_same(content1, content2):
    return content1.strip() == content2.strip()

def handle_duplicate_file(existing_file, new_content):
    if is_file_content_same(existing_file['content'], new_content):
        return False, "File already exists with identical content"
    
    return True, "File content updated"

def log_file_upload(file, conversation_id, user_id):
    filename = secure_filename(file.filename)
    extension = filename.split('.')[-1].lower()
    
    if extension not in ALLOWED_EXTENSIONS:
        return None

    new_content = file.read().decode('utf-8', errors='ignore')

    conversation = get_conversation(user_id, conversation_id)
    incoming_files = conversation.get('incoming_files', [])

    for idx, existing_file in enumerate(incoming_files):
        if existing_file['filename'] == filename:
            if not is_file_content_same(existing_file['content'], new_content):
                incoming_files[idx]['content'] = new_content
                
                save_conversation(
                    user_id, conversation_id,
                    conversation.get('conversation', []),
                    incoming_files = incoming_files,
                    name = conversation.get('name')
                )

            return {
                'filename': filename,
                'status': 'success',
                'message': 'File processed successfully'
            }

    result = {
        'filename': filename,
        'content': new_content,
        'extension': extension
    }
    
    incoming_files.append(result)

    save_conversation(
        user_id, conversation_id,
        conversation.get('conversation', []),
        incoming_files = incoming_files,
        name = conversation.get('name')
    )

    return {
        'filename': filename,
        'status': 'success',
        'message': 'File processed successfully'
    }

def remove_file_from_conversation(filename, conversation_id, user_id):
    conversation = get_conversation(user_id, conversation_id)
    incoming_files = conversation.get('incoming_files', [])
    attached_files = conversation.get('attached_files', [])

    incoming_files = [f for f in incoming_files if f['filename'] != filename]

    save_conversation(
        user_id, conversation_id,
        conversation.get('conversation', []),
        incoming_files=incoming_files,
        attached_files=attached_files,
        name=conversation.get('name')
    )

    print(f"File removed (incoming only): {filename}. Updated incoming files: {incoming_files}, attached files: {attached_files}")
    return {'status': 'success', 'message': 'File removed from incoming files only'}
