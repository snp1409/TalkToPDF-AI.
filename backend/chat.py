import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from langchain_core.prompts import PromptTemplate

load_dotenv()

# --- THE AUTHORITATIVE UNIVERSAL TEMPLATE ---
template = """You are a highly accurate Document Analyst.

TASK: Analyze the provided document context to answer the user's question.

1. GLOBAL COVERAGE: You have been provided with excerpts from different parts of the document. Use them to provide a complete and organized answer.
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

    # --- CLOUD OPTIMIZED RETRIEVAL ---
    # We detect if the user wants a broad overview
    is_summary = any(w in query.lower() for w in ["summary", "overview", "all", "entire", "everything"])

    if is_summary:
        # A. Get diverse semantic matches (Reduced k for RAM safety)
        semantic_docs = vector_store.similarity_search(query, k=8, pre_filter={"username": {"$eq": username}})
        
        # B. Get the very first 2 chunks (The Intro)
        head_docs = list(collection.find({"username": username}).sort("_id", 1).limit(2))
        
        # C. Get the very last 2 chunks (The Hobbies/Conclusion)
        tail_docs = list(collection.find({"username": username}).sort("_id", -1).limit(2))

        # Combine all unique text into a single context string
        all_text = []
        # We combine head, semantic, and tail for full document coverage
        for d in (head_docs + semantic_docs + tail_docs):
            # Check if it's a LangChain Document or a raw MongoDB dictionary
            txt = d.page_content if hasattr(d, 'page_content') else d.get("text", d.get("page_content", ""))
            if txt and txt not in all_text: 
                all_text.append(txt)
        
        context_text = "\n\n".join(all_text)
    else:
        # Standard search for specific questions (Reduced k to 5 for speed/RAM)
        docs = vector_store.similarity_search(query, k=5, pre_filter={"username": {"$eq": username}})
        context_text = "\n\n".join([d.page_content for d in docs])

    # Build the final prompt
    final_prompt = template.format(context=context_text, question=query)

    try:
        response = llm.invoke(final_prompt)
        return response.content
    except Exception as e:
        # Catch quota or system errors
        if "429" in str(e):
            return "⚠️ API Quota reached. Please wait 60 seconds."
        return f"⚠️ System Error: {str(e)}"

if __name__ == "__main__":
    q = input("Question: ")
    print(ask_question(q, "test_user"))