import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from langchain_core.prompts import PromptTemplate

load_dotenv()

# Optimized Template for Speed
template = """You are a professional Document Assistant.
Use the provided context to answer the user's question accurately.

1. If the information is in the context, provide a clear, bulleted answer.
2. If it's a greeting (hi, hello), greet them and mention you are ready to analyze the file.
3. If the answer is not there, say: "I'm sorry, I couldn't find that specific information in this document."

Context:
{context}

Question: {question}

Assistant Reply:"""

def ask_question(query, username, filename="None"):
    # 1. Handle Pre-Upload State
    if filename == "None" or not filename:
        return f"Hello {username}! I am ready. Please upload a PDF in the sidebar to begin analysis."

    client = MongoClient(os.getenv("MONGO_URI"))
    collection = client["pdf_bot_db"]["pdf_chunks"]

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", 
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # We use Flash because it is the fastest model available
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-flash-latest", 
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.1
    )

    vector_store = MongoDBAtlasVectorSearch(
        collection=collection,
        embedding=embeddings,
        index_name="vector_index"
    )

    # --- CLOUD OPTIMIZATION ---
    # We use k=5. This ensures the prompt is small and the AI 
    # responds very quickly to avoid 'Connection Lost' timeouts.
    try:
        docs = vector_store.similarity_search(
            query, 
            k=5, 
            pre_filter={"username": {"$eq": username}}
        )
        
        if not docs:
            return "I couldn't find any data for your account. Please try re-uploading the file."

        context_text = "\n\n".join([doc.page_content for doc in docs])
        final_prompt = template.format(context=context_text, question=query)

        response = llm.invoke(final_prompt)
        return response.content if response.content else "AI generated an empty response. Please try again."

    except Exception as e:
        if "429" in str(e):
            return "⚠️ API limit reached. Please wait 60 seconds."
        return f"Logic Error: {str(e)}"

if __name__ == "__main__":
    print(ask_question("Hi", "test_user"))