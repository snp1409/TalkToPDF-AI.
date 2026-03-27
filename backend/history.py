import os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["pdf_bot_db"]
history_collection = db["chat_history"]

def save_chat_message(username, filename, role, text):
    chat_doc = {
        "username": username,
        "filename": filename,
        "role": role,
        "text": text,
        "timestamp": datetime.utcnow()
    }
    history_collection.insert_one(chat_doc)

def get_chat_history(username, filename):
    chats = history_collection.find(
        {"username": username, "filename": filename}
    ).sort("timestamp", 1)
    return [{"role": c["role"], "text": c["text"]} for c in chats]

def get_user_files(username):
    files = history_collection.distinct("filename", {"username": username})
    return files if files else []

# NEW: Function to remove chat history for a specific file
def delete_file_history(username, filename):
    history_collection.delete_many({"username": username, "filename": filename})
    print(f"Deleted chat history for {filename}")