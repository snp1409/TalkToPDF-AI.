import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from langchain_core.prompts import PromptTemplate

load_dotenv()

template = """You are a professional Document AI Assistant. 
Answer the user's question using ONLY the provided context.

Context: {context}
Question: {question}
Assistant Reply:"""

def ask_question(query, username, filename="None"):
    if filename == "None" or not filename:
        return f"Hello {username}! I am ready. Please upload a PDF to begin."

    client = MongoClient(os.getenv("MONGO_URI"))
    collection = client["pdf_bot_db"]["pdf_chunks"]

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", 
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # --- MODEL FIX ---
    # We use 'gemini-flash-latest' as it was confirmed in your authorized list
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-flash-latest", 
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.2
    )

    vector_store = MongoDBAtlasVectorSearch(
        collection=collection,
        embedding=embeddings,
        index_name="vector_index"
    )

    docs = vector_store.similarity_search(query, k=6, pre_filter={"username": {"$eq": username}})
    context_text = "\n\n".join([doc.page_content for doc in docs])
    final_prompt = template.format(context=context_text, question=query)

    try:
        response = llm.invoke(final_prompt)
        # Handle different response formats
        raw_content = response.content
        if isinstance(raw_content, list):
            return "".join([part['text'] if isinstance(part, dict) else str(part) for part in raw_content])
        return str(raw_content)
    except Exception as e:
        if "429" in str(e): return "⚠️ Quota reached. Wait 60 seconds."
        return f"AI Error: {str(e)}"

if __name__ == "__main__":
    print(ask_question("Hi", "test_user"))