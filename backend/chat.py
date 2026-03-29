import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from langchain_core.prompts import PromptTemplate

load_dotenv()

# Universal prompt for any document
template = """You are a professional Document AI Assistant. 
Answer the user's question using ONLY the provided context.

1. If the user greets you (hello, hi), greet them back politely.
2. If the answer is in the context, be detailed and use bullet points.
3. If the answer is missing, say: "I'm sorry, I couldn't find that in this document."

Context:
{context}

Question: {question}

Assistant Reply:"""

def ask_question(query, username, filename="None"):
    # 1. Handle Pre-Upload State
    if filename == "None" or not filename:
        return f"Hello {username}! I am ready. Please upload a PDF to begin."

    client = MongoClient(os.getenv("MONGO_URI"))
    collection = client["pdf_bot_db"]["pdf_chunks"]

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", 
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # Using gemini-1.5-flash for maximum speed in the cloud
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-1.5-flash", 
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.2
    )

    vector_store = MongoDBAtlasVectorSearch(
        collection=collection,
        embedding=embeddings,
        index_name="vector_index"
    )

    # 2. Optimized Retrieval
    # We use k=7 to provide good context while keeping the response fast
    docs = vector_store.similarity_search(
        query, 
        k=7, 
        pre_filter={"username": {"$eq": username}}
    )
    
    context_text = "\n\n".join([doc.page_content for doc in docs])
    final_prompt = template.format(context=context_text, question=query)

    try:
        response = llm.invoke(final_prompt)
        
        # --- THE FIX FOR MESSY JSON OUTPUT ---
        raw_content = response.content
        
        # Check if the response is a list (the messy format you saw)
        if isinstance(raw_content, list):
            # Extract the 'text' part from each item in the list
            clean_text = ""
            for part in raw_content:
                if isinstance(part, dict) and 'text' in part:
                    clean_text += part['text']
                else:
                    clean_text += str(part)
            return clean_text
        
        # If it's already a clean string, return it
        return str(raw_content)

    except Exception as e:
        if "429" in str(e):
            return "⚠️ Daily limit reached. Please try again in a bit."
        return f"Logic Error: {str(e)}"

if __name__ == "__main__":
    print(ask_question("Hi", "test_user"))