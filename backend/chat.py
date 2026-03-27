import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from langchain.prompts import PromptTemplate

load_dotenv()

template = """You are a highly accurate Document Analyst.

TASK: Analyze the provided document context to answer the user's question.

1. GLOBAL COVERAGE: You have been provided with excerpts from the beginning, middle, and end of the document. Use them to provide a complete answer.
2. ACCURACY: If the information is present, summarize it clearly. 
3. HONESTY (The No-Guess Rule): If the information is absolutely NOT in the provided context, say: 
"I have carefully scanned the document and I can confirm that this specific information is not mentioned in this file. Please try with some other prompt that is accurate."
4. STRUCTURE: Use bold headings and bullet points.

Context:
{context}

Question: {question}

Assistant Reply:"""

def ask_question(query, username, filename="None"):
    if filename == "None" or not filename:
        return f"Hello {username}! I am your AI. Please upload a document to begin."

    client = MongoClient(os.getenv("MONGO_URI"))
    collection = client["pdf_bot_db"]["pdf_chunks"]

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", 
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-flash-latest", 
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0 
    )

    vector_store = MongoDBAtlasVectorSearch(
        collection=collection,
        embedding=embeddings,
        index_name="vector_index"
    )

    # --- THE "TOTAL SCAN" RETRIEVAL ---
    is_summary = any(w in query.lower() for w in ["summary", "overview", "all", "entire"])

    if is_summary:
        # A. Get diverse semantic matches
        semantic_docs = vector_store.similarity_search(query, k=10, pre_filter={"username": {"$eq": username}})
        
        # B. Get the very first 5 chunks (The Intro)
        head_docs = list(collection.find({"username": username}).sort("_id", 1).limit(5))
        
        # C. Get the very last 5 chunks (The Hobbies/Conclusion)
        tail_docs = list(collection.find({"username": username}).sort("_id", -1).limit(5))

        # Combine all unique text
        all_text = []
        for d in (head_docs + semantic_docs + tail_docs):
            txt = d.page_content if hasattr(d, 'page_content') else d.get("text", d.get("page_content", ""))
            if txt not in all_text: all_text.append(txt)
        
        context_text = "\n\n".join(all_text)
    else:
        # Standard search for specific questions
        docs = vector_store.similarity_search(query, k=10, pre_filter={"username": {"$eq": username}})
        context_text = "\n\n".join([d.page_content for d in docs])

    final_prompt = template.format(context=context_text, question=query)

    try:
        response = llm.invoke(final_prompt)
        return response.content
    except Exception as e:
        return f"⚠️ Error: {str(e)}"