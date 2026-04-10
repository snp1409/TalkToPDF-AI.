import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from langchain_core.prompts import PromptTemplate

load_dotenv()

# --- THE UNIVERSAL MASTER TEMPLATE ---
# Designed to be descriptive and long for any document type
template = """You are an Advanced Document Intelligence System. 

TASK: Analyze the provided excerpts from a document to answer the user's question with high detail and professional clarity.

1. COMPREHENSIVE RESPONSE: Provide long, structured, and detailed answers. Use multiple bullet points and bold text for key terms.
2. UNIVERSAL SCOPE: Whether the document is a resume, a report, or a manual, extract all relevant sections mentioned in the context.
3. NO HALLUCINATION: If the information is not in the provided excerpts, say: "I have scanned the document and this specific information is not mentioned in the current context."
4. GREETING: If it's a greeting, reply politely as a universal document assistant.

Context Excerpts:
{context}

User Question: {question}

Detailed Assistant Reply:"""

def ask_question(query, username, filename="None"):
    if filename == "None" or not filename:
        return f"Hello {username}! I am your Universal Document AI. Please upload any PDF to begin."

    client = MongoClient(os.getenv("MONGO_URI"))
    collection = client["pdf_bot_db"]["pdf_chunks"]

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", 
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-flash-latest", 
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.2 # Small creativity for better flow, but still factual
    )

    vector_store = MongoDBAtlasVectorSearch(
        collection=collection,
        embedding=embeddings,
        index_name="vector_index"
    )

    # --- THE UNIVERSAL SEARCH ENGINE ---
    # We detect if the user wants a broad overview or specific detail
    is_broad = any(w in query.lower() for w in ["summary", "overview", "all", "everything", "details"])
    
    # We use k=15 to give the AI enough data for LONG responses without crashing Render's RAM
    top_k = 15 if is_broad else 8

    try:
        docs = vector_store.similarity_search(
            query, 
            k=top_k, 
            pre_filter={"username": {"$eq": username}}
        )
        
        context_text = "\n\n".join([doc.page_content for doc in docs])
        final_prompt = template.format(context=context_text, question=query)

        response = llm.invoke(final_prompt)
        
        # --- THE "CODE BREAKING" FIX (STRICT PARSING) ---
        # This handles the messy JSON format from your screenshots
        raw_content = response.content
        
        if isinstance(raw_content, list):
            # Extract text from the list of dicts/objects
            processed_text = ""
            for item in raw_content:
                if isinstance(item, dict) and 'text' in item:
                    processed_text += item['text']
                else:
                    processed_text += str(item)
            return processed_text.strip()
        
        return str(raw_content).strip()

    except Exception as e:
        if "429" in str(e):
            return "⚠️ API Quota reached. Please wait 60 seconds."
        return f"Technical Error: {str(e)}"