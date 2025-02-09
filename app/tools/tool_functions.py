from datetime import datetime

from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

import os
from dotenv import load_dotenv

load_dotenv()

last_key = None

equations = []
searches = []

def plot_graph(equation, key):
    global last_key, equations

    if last_key != key:
        equations.clear()

    last_key = key
    equations.append(equation)
    
    return ({
        "equations": equations,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

def research(query, key):
    global last_key, searches

    if last_key != key:
        searches.clear()
    
    last_key = key

    # search the query

    search = []

    client = genai.Client(api_key = os.getenv("GOOGLE_GENAI_API_KEY"))
    model_id = "gemini-2.0-flash"

    google_search_tool = Tool(
        google_search = GoogleSearch()
    )

    response = client.models.generate_content(
        model = model_id,
        contents = query,
        config = GenerateContentConfig(
            tools = [google_search_tool],
            response_modalities = ["TEXT"],
        )
    )

    for each in response.candidates[0].content.parts:
        search.append(each.text)

    searches.extend(search)

    return ({
        "query": searches
    })

# define functions for each tool to be used in the model

def graph_tool():
    return (
        {
            "type": "function",
            "function": {
                "name": "plot_graph",
                "description": "Plots a mathematical graph based on the given equation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "equation": {
                            "type": "string",
                            "description": "The equation to plot, e.g. y = x^2",
                        }
                    },
                    "required": ["equation"]
                }
            }
        }
    )

def research_tool():
    return (
        {
            "type": "function",
            "function": {
                "name": "research",
                "description": "Researches a topic and returns the answer",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to research, e.g. 'What was the latest football game played in the U.S., and what were the final scores?'",
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    )
