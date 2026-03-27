import os
import time
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch

load_dotenv()

def save_to_mongodb(chunks, username, filename):
    print(f"--- Step 3: Connecting to MongoDB for user: {username} ---")
    client = MongoClient(os.getenv("MONGO_URI"))
    collection = client["pdf_bot_db"]["pdf_chunks"]

    # Clear old version of THIS SAME FILE if it exists for this user
    collection.delete_many({"username": username, "metadata.filename": filename})

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", 
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    # Add both username AND filename to every chunk
    for chunk in chunks:
        chunk.metadata["username"] = username
        chunk.metadata["filename"] = filename

    batch_size = 25 
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        print(f"Uploading batch {i//batch_size + 1}...")
        MongoDBAtlasVectorSearch.from_documents(
            documents=batch, embedding=embeddings,
            collection=collection, index_name="vector_index"
        )
        if i + batch_size < len(chunks):
            time.sleep(60)

    print(f"✅ Vectors stored for {filename}.")

# NEW: Function to remove vectors from the database
def delete_document_vectors(username, filename):
    client = MongoClient(os.getenv("MONGO_URI"))
    collection = client["pdf_bot_db"]["pdf_chunks"]
    result = collection.delete_many({
        "username": username, 
        "metadata.filename": filename
    })
    print(f"Deleted {result.deleted_count} vectors for {filename}")