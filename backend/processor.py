import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def process_pdf(file_path):
    # 1. Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: The file {file_path} was not found!")
        return None

    print(f"--- Step 1: Loading PDF: {file_path} ---")
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    print(f"Successfully loaded {len(pages)} pages.")

    # 2. Setup the Splitter (The "Chunking" logic)
    # We use 1000 characters per chunk with a 100 character overlap
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,  # Smaller chunks = more detail
        chunk_overlap=100, # Better connection between chunks
        length_function=len
    )

    # 3. Split the document into chunks
    print("--- Step 2: Splitting into chunks ---")
    chunks = text_splitter.split_documents(pages)
    
    print(f"Done! Created {len(chunks)} chunks.")
    
    # 4. Show a sample of the first chunk to see if it worked
    if chunks:
        print("\n--- Preview of Chunk #1 ---")
        print(chunks[0].page_content[:300] + "...") # Show first 300 characters
        print("---------------------------\n")
        
    return chunks

if __name__ == "__main__":
    # This runs only when you execute the file directly
    process_pdf("test.pdf")