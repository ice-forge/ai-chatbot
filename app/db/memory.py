import os
import json

from app.db.models import send_message_to_openai, get_model_by_name

MEMORY = os.getenv('MEMORY', 'False').lower() in ['true', '1', 't']

def should_be_global_memory(memory_item, model):
    system_prompt = """
        You are a helpful AI assistant that determines if this information stored as a memory should be global (available to all conversations in an ai chatbot application) or remain local to the current conversation.
        
        RULES FOR GLOBAL MEMORY:

        - Personal facts about the user (name, preferences, important details)
        - Long-term relevant information
        - Information that would be useful across all conversations
        
        CRITICAL INSTRUCTION:
        
        - Return only "global" or "local" as your answer.
    """

    result = send_message_to_openai([], [], memory_item, model, system_prompt)
    return result['response'].lower().strip() == "global"

def is_duplicate_memory(memory_item, local_memory, global_memory):
    return memory_item in local_memory or memory_item in global_memory

def summarize_memory(local_memory, global_memory, user_message, model_name):
    if not MEMORY:
        return "None"
    
    model = get_model_by_name(model_name)

    system_prompt = f"""
        You are a helpful AI assistant that analyzes interactions and determine if any new information should be stored in memory.
        
        STRICT RULES FOR NOT OUTPUTTING ANYTHING:

        1. If the information exists in ANY form in either Local or Global memory
        2. If the user is asking questions rather than providing information
        3. If the user is asking about known information (e.g., "what's my name?")
        4. If the information is a general fact or knowledge (e.g., "Paris is in France")
        5. If the information is similar or related to existing memories
        6. If the user is confirming already known information
        
        ONLY OUTPUT when ALL these conditions are met:

        1. The information is completely new
        2. The information is about the user's personal details, preferences, or important facts
        3. The information would be valuable in future conversations
        4. The information is not derivable from existing memories
        
        FORMAT FOR OUTPUT:

        - Keep it brief and factual
        - Start with "The user's..." or similar clear identifier
        - Only include the new information
        
        CURRENT MEMORY CONTEXT:

        - Local Memory: {local_memory}
        - Global Memory: {global_memory}

        CRITICAL INSTRUCTION:

        - If no new information needs to be stored, return None (not an empty string, not a space, literally None)
        - Only output text if there is actually new information to store
    """

    summary = send_message_to_openai(local_memory, global_memory, user_message, model, system_prompt)

    if summary['response'] == "None" or summary['status'] == 'error':
        return "None"

    if not is_duplicate_memory(summary, local_memory, global_memory):
        if should_be_global_memory(summary, model):
            global_memory.append(summary)
            save_global_memory(global_memory)

            return "None"
        
        return summary
    
    return "None"
    
def load_global_memory():
    with open(os.path.join(os.path.dirname(__file__), '../storage/db/models.json'), 'r') as f:
        return json.load(f).get('global_memory', [])

def save_global_memory(global_memory):
    with open(os.path.join(os.path.dirname(__file__), '../storage/db/models.json'), 'r+') as f:
        data = json.load(f)
        data['global_memory'] = global_memory
        
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
