import openai

import requests
import json
import uuid

from app.tools.tool_functions import graph_tool, research_tool, plot_graph, research

import os
from dotenv import load_dotenv

load_dotenv()

def parse_bool_env(name, default='False'):
    return os.getenv(name, default).strip().lower() in ['true', '1', 't', 'yes']

# Model configuration

FILES = parse_bool_env('FILES') # Enables or disables file context

MEMORY = parse_bool_env('MEMORY') # Enables for disables local and global memory

LOCAL_MEMORY = parse_bool_env('LOCAL_MEMORY')
GLOBAL_MEMORY = parse_bool_env('GLOBAL_MEMORY')

TOOLS = parse_bool_env('TOOLS') # Enables or disables graph and research tools

GRAPH = parse_bool_env('GRAPH')
RESEARCH = parse_bool_env('RESEARCH')

# Paths

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../" * 2))
LOCAL_STORAGE_PATH = os.path.join(ROOT_PATH, "storage")

def system_prompt(local_memory, global_memory, files, model_tools, model):
    global FILES, MEMORY, LOCAL_MEMORY, GLOBAL_MEMORY, TOOLS, GRAPH, RESEARCH
    
    SYSTEM_PROMPT = ""
    
    if MEMORY and (LOCAL_MEMORY or GLOBAL_MEMORY) and (local_memory or global_memory): # memory
        SYSTEM_PROMPT += f"\n\nMEMORY INSTRUCTIONS:"

        if LOCAL_MEMORY and local_memory:
            SYSTEM_PROMPT += f"\n\nLocal memory refers to temporary, context-specific information relevant to the current conversation. Local Memory: {local_memory}."
        
        if GLOBAL_MEMORY and global_memory:
            SYSTEM_PROMPT += f"\n\nGlobal memory refers to personal facts about the user, long-term relevant details, or information that would be helpful in future interactions. Global Memory: {global_memory}."
    
    if FILES and files: # files
        SYSTEM_PROMPT += f"\n\nFILES INSTRUCTIONS:\n\nFiles are attached to this message in a json format. Files: {files}."

    if TOOLS and (GRAPH or RESEARCH) and model['supports_tools'] and model_tools: # tools
        SYSTEM_PROMPT += f"\n\nTOOLS INSTRUCTIONS:"

        if GRAPH and "graph" in model_tools:
            SYSTEM_PROMPT += f"\n\nThe Desmos Calculator tool for graphing is being used. If the user asks you to graph an equation, use the plot_graph() function. For example, plot_graph('y = x^2')."

        if RESEARCH and "research" in model_tools:
            SYSTEM_PROMPT += f"\n\nThe Research tool is being used. If the user asks you to research something, or you need to search something for up to date information (such as the day or time), use the research() function. For example, research('What was the latest football game played in the U.S., and what were the final scores?').\n\n"
    elif (model['supports_tools']):
        SYSTEM_PROMPT += f"\n\nIf the user asks you to graph equations, research online information, or you need to provide real-time information (such as the day or time), prompt the user to use the '@graph' or '@research' tools, respectively."


    return SYSTEM_PROMPT

def send_message_to_openai(local_memory, global_memory, user_message, model, model_prompt = None, files = None, tools = None):
    global FILES, MEMORY, LOCAL_MEMORY, GLOBAL_MEMORY, TOOLS, GRAPH, RESEARCH
    
    SYSTEM_PROMPT = model_prompt

    if SYSTEM_PROMPT is None:
        SYSTEM_PROMPT = system_prompt(local_memory, global_memory, files, tools, model)

    try:
        client = openai.AzureOpenAI(
            api_key = os.getenv(model['env_api_key']),
            api_version = os.getenv(model['env_api_version']),
            azure_endpoint = os.getenv(model['env_endpoint'])
        )

        deployment_name = os.getenv(model['env_deployment_name'])

        payload = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_message
            }
        ]

        tools_result = {}

        if TOOLS and (GRAPH or RESEARCH) and model['supports_tools'] and tools:
            model_tools = []

            if GRAPH and "graph" in tools:
                model_tools.append(graph_tool())

            if RESEARCH and "research" in tools:
                model_tools.append(research_tool())

            tools_response = client.chat.completions.create(
                model = deployment_name,
                messages = payload,
                tools = model_tools,
                tool_choice = "auto"
            )

            response_message = tools_response.choices[0].message
            payload.append(response_message)

            current_key = str(uuid.uuid4())

            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    if tool_call.function.name == "plot_graph":
                        function_args = json.loads(tool_call.function.arguments)
                        graph_equation = function_args.get("equation")
                        
                        graph_response = plot_graph(equation = graph_equation, key = current_key)

                        payload.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": "plot_graph",
                            "content": json.dumps({
                                "equation": graph_equation,
                                "timestamp": graph_response["timestamp"]
                            })
                        })

                        tools_result["graph"] = graph_response

                    if tool_call.function.name == "research":
                        function_args = json.loads(tool_call.function.arguments)
                        research_query = function_args.get("query")

                        research_response = research(query = research_query, key = current_key)

                        payload.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": "research",
                            "content": json.dumps({
                                "query": research_response["query"]
                            })
                        })

                        tools_result["research"] = research_response

        message_response = client.chat.completions.create(
            model = deployment_name,
            messages = payload,
        )

        result = message_response.choices[0].message.content

        return {
            "status": "success",
            "response": result,
            "tools": tools_result
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
            "response": f"Unexpected response structure from API.\n\n{str(ex)}",
            "error": str(ex),
            "error_type": "api_response_error"
        }

    except Exception as ex:
        return {
            "status": "error",
            "response": f"An unexpected error occurred.\n\n{str(ex)}",
            "error": str(ex),
            "error_type": "general_error"
        }

MODEL_HANDLERS = {
    'send_message_to_openai': send_message_to_openai

    # <-- Add your model handlers here by referencing their handler from the `models.json` file, then inserting the name of the model function, listed above -->
}

def load_models():
    models_path = os.path.join(LOCAL_STORAGE_PATH, "models.json")

    with open(models_path, 'r') as f:
        return json.load(f)['models']

def get_model_by_name(name):
    models = load_models()
    return next((model for model in models if model['name'] == name), None)
