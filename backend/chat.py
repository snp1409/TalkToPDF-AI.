import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from langchain_core.prompts import PromptTemplate

load_dotenv()

# THE ULTIMATE PROMPT: Forces accuracy and long responses
template = """You are a Master Document Analyst. Your responses are known for being detailed, accurate, and perfectly organized.

TASK: Use the provided context excerpts to answer the user's question. 

1. COMPREHENSIVENESS: Provide a long, deep answer. If it is a summary, cover every section from the context.
2. ACCURACY: Do not guess. Look at the specific details like dates, names, and technical stacks.
3. STRUCTURE: Use bold headings and bullet points for every response.
4. GREETING: If it's a 'hi' or 'hello', greet them as the TalkToPDF AI and mention the file name.

Context Excerpts:
{context}

User Question: {question}

Detailed Assistant Reply:"""

def ask_question(query, username, filename="None"):
    if filename == "None" or not filename:
        return f"Hello {username}! I am TalkToPDF. Please upload a document to begin our analysis."

    client = MongoClient(os.getenv("MONGO_URI"))
    collection = client["pdf_bot_db"]["pdf_chunks"]

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", 
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # --- FIX APPLIED HERE: Updated to 2.5-flash ---
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash", 
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.1 # Low temperature for high accuracy
    )

    vector_store = MongoDBAtlasVectorSearch(collection=collection, embedding=embeddings, index_name="vector_index")

    # --- PERMANENT ACCURACY FIX: BOUNDARY-PINNED RETRIEVAL ---
    # 1. Get Semantic Matches (Top 6)
    semantic_docs = vector_store.similarity_search(query, k=6, pre_filter={"username": {"$eq": username}})
    
    # 2. Get the First 3 Chunks (Start of Doc)
    head_docs = list(collection.find({"username": username}).sort("_id", 1).limit(3))
    
    # 3. Get the Last 3 Chunks (End of Doc)
    tail_docs = list(collection.find({"username": username}).sort("_id", -1).limit(3))

    # Combine all unique text chunks
    all_chunks =[]
    seen_text = set()
    
    for doc in (head_docs + semantic_docs + tail_docs):
        # Handle different data types (Mongo vs Langchain)
        text = doc.page_content if hasattr(doc, 'page_content') else doc.get("text", doc.get("page_content", ""))
        if text and text not in seen_text:
            all_chunks.append(text)
            seen_text.add(text)
    
    context_text = "\n\n".join(all_chunks)
    final_prompt = template.format(context=context_text, question=query)

    try:
        # We use invoke with a timeout hint
        response = llm.invoke(final_prompt)
        
        # Strict parsing to handle the 'messy code' error
        content = response.content
        if isinstance(content, list):
            return "".join([p.get('text', str(p)) if isinstance(p, dict) else str(p) for p in content])
        return str(content)

    except Exception as e:
        if "429" in str(e): return "⚠️ API Quota reached. Please wait 60 seconds."
        return f"AI Logic Error: {str(e)}"