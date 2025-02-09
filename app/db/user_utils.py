import json
import os

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../" * 2))
LOCAL_STORAGE_PATH = os.path.join(ROOT_PATH, "storage")

INDENT = 4

users_path = os.path.join(LOCAL_STORAGE_PATH, "users.json")

if not os.path.exists(users_path):
    with open(users_path, 'w') as file:
        json.dump([], file, indent=INDENT)

def load_users():
    with open(users_path, 'r') as file:
        return json.load(file)

def save_users(users):
    with open(users_path, 'w') as file:
        json.dump(users, file, indent = INDENT)
