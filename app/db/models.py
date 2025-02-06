import ollama

import requests
import json

import os
from dotenv import load_dotenv

load_dotenv()

def parse_bool_env(name, default='False'):
    return os.getenv(name, default).strip().lower() in ['true', '1', 't', 'yes']

MEMORY = parse_bool_env('MEMORY')
FILES = parse_bool_env('FILES')
LOCAL_MEMORY = parse_bool_env('LOCAL_MEMORY')
GLOBAL_MEMORY = parse_bool_env('GLOBAL_MEMORY')

def system_prompt(local_memory, global_memory, files):
    SYSTEM_PROMPT = ""
    
    if MEMORY and (LOCAL_MEMORY or GLOBAL_MEMORY) and (local_memory or global_memory):
        SYSTEM_PROMPT += f"\n\nMEMORY INSTRUCTIONS:"

        if LOCAL_MEMORY and local_memory:
            SYSTEM_PROMPT += f"\n\nLocal memory refers to temporary, context-specific information relevant to the current conversation. Local Memory: {local_memory}."
        
        if GLOBAL_MEMORY and global_memory:
            SYSTEM_PROMPT += f"\n\nGlobal memory refers to personal facts about the user, long-term relevant details, or information that would be helpful in future interactions. Global Memory: {global_memory}."
    
    if FILES and files:
        SYSTEM_PROMPT += f"\n\nFILES INSTRUCTIONS:\n\nFiles are attached to this message in a json format. Files: {files}."

    return SYSTEM_PROMPT

def send_message_to_openai(local_memory, global_memory, user_message, model, model_prompt = None, files = None):
    SYSTEM_PROMPT = model_prompt

    if SYSTEM_PROMPT == None:
        SYSTEM_PROMPT = system_prompt(local_memory, global_memory, files)

    try:
        AZURE_OPENAI_API_KEY = os.getenv(model['env_api_key'])
        AZURE_OPENAI_ENDPOINT = os.getenv(model['env_endpoint'])
        
        headers = {
            "Content-Type": "application/json",
            "api-key": AZURE_OPENAI_API_KEY,
        }

        payload = {
            "messages": [
                {
                    "role": "system", 
                    "content": [
                        {
                            "type": "text", 
                            "text": SYSTEM_PROMPT
                        }
                    ]
                },
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text", 
                            "text": f"question: {user_message}"
                        }
                    ]
                }
            ]
        }

        response = requests.post(AZURE_OPENAI_ENDPOINT, headers = headers, json = payload)
        response.raise_for_status()

        result = response.json()['choices'][0]['message']['content']

        return {
            "status": "success",
            "response": result,
            "error": None
        }

    except requests.exceptions.RequestException as ex:
        return {
            "status": "error",
            "response": f"An HTTP error occurred. Please ensure your .env files are properly configured.\n\n{str(ex)}",
            "error": str(ex),
            "error_type": "http_error"
        }

    except KeyError as ex:
        return {
            "status": "error",
            "response": "Unexpected response structure from API.",
            "error": str(ex),
            "error_type": "api_response_error"
        }

    except Exception as ex:
        return {
            "status": "error",
            "response": "An unexpected error occurred.",
            "error": str(ex),
            "error_type": "general_error"
        }
    
def send_message_to_llama(local_memory, global_memory, user_message, model, model_prompt = None, files = None):
    SYSTEM_PROMPT = model_prompt

    if SYSTEM_PROMPT == None:
        SYSTEM_PROMPT = system_prompt(local_memory, global_memory, files)

    try:
        ollama.pull('llama3.2:1b')

        stream = ollama.chat(
            model = 'llama3.2:1b',
            messages=[
                {
                    'role': 'system',
                    'content': model["system_prompt"]
                },
                {
                    'role': 'user',
                    'content': f"question: {user_message}. System Prompt: {SYSTEM_PROMPT}"
                }
            ],
            stream = True
        )

        full_response = ""

        for chunk in stream:
            content = chunk['message']['content']
            full_response += content

        return {
            "status": "success",
            "response": full_response,
            "error": None
        }
    
    except Exception as ex:
        return {
            "status": "error",
            "response": "An unexpected error occurred.",
            "error": str(ex),
            "error_type": "general_error"
        }
    
MODEL_HANDLERS = {
    'send_message_to_openai': send_message_to_openai,
    'send_message_to_llama': send_message_to_llama

    # <-- Add your model handlers here by referencing their handler from the `models.json` file, then inserting the name of the model function, listed above -->
}

def load_models():
    with open(os.path.join(os.path.dirname(__file__), '../storage/db/models.json'), 'r') as f:
        return json.load(f)['models']

def get_model_by_name(name):
    models = load_models()
    return next((model for model in models if model['name'] == name), None)
