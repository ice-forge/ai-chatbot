from app.db.conversation_utils import save_conversation, get_conversation
from app.utils.formatting import format_ai_message

from app.db.models import load_models, get_model_by_name, MODEL_HANDLERS
from app.db.memory import summarize_memory

models = load_models()

def handle_send_message(user_id, conversation_id, user_message, selected_model, files=[], display_files=[]):
    try:
        data = get_conversation(user_id, conversation_id)

        attached_files = None
        incoming_files = data.get('incoming_files', [])

        if data.get('incoming_files'):
            attached_files = data.get('attached_files', [])

            for incoming_file in incoming_files:
                duplicate = False

                for attached_file in attached_files:
                    if attached_file['filename'] == incoming_file['filename']:
                        if attached_file['content'] == incoming_file['content']:
                            duplicate = True
                            break

                        else:
                            attached_file['content'] = incoming_file['content']
                            duplicate = True

                            break

                if not duplicate:
                    attached_files.append(incoming_file)

            data['incoming_files'].clear()

        conversation = data.get('conversation', [])
        local_memory = data.get('local_memory', [])
        global_memory = data.get('global_memory', [])

        conversation.append({
            "role": "user", 
            "content": [{"type": "text", "text": user_message}], 
            "files": display_files
        })

        result = send_message_to_model(local_memory, global_memory, user_message, selected_model, files)

        if result["status"] == "success":
            result["response"] = format_ai_message(result["response"])

        conversation.append({
            "role": "system", 
            "content": [{"type": "text", "text": result["response"]}], 
            "model": selected_model
        })

        summary = None

        if not result['status'] == 'error':
            memory = summarize_memory(local_memory, global_memory, user_message, selected_model)

            if not memory == "None":
                summary = memory

        if summary:
            local_memory.append(summary)

        save_conversation(
            user_id,

            conversation_id,
            conversation,

            name = data.get('name'),

            local_memory = local_memory,
            global_memory = global_memory,

            attached_files = attached_files,
            incoming_files = data['incoming_files']
        )

        return result

    except Exception as e:
        return {
            "status": "error",
            "response": "An error occurred while processing your message.",
            "error": str(e),
            "error_type": "processing_error"
        }

def send_message_to_model(local_memory, global_memory, user_message, model_name, files):
    model = get_model_by_name(model_name)

    if not model:
        return {
            "status": "error",
            "response": "Please select a model and re-submit your request.",
            "error": "No model selected",
            "error_type": "model_selection"
        }

    handler_name = model.get('handler')
    handler = MODEL_HANDLERS.get(handler_name)

    if not handler:
        return {
            "status": "error",
            "response": f"No valid handler found for model: {model_name}.",
            "error": f"Handler '{handler_name}' is not registered in MODEL_HANDLERS",
            "error_type": "handler_not_found"
        }
    
    return handler(local_memory, global_memory, user_message, model, files=files)
