from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os

from processor import process_pdf
from database import save_to_mongodb, delete_document_vectors
from chat import ask_question
from history import save_chat_message, get_chat_history, get_user_files, delete_file_history

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "TalkToPDF Cloud Server is Active"}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), username: str = Form(...)):
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        chunks = process_pdf(file_path)
        save_to_mongodb(chunks, username, file.filename)
        os.remove(file_path)
        return {"message": "Success", "filename": file.filename}
    except Exception as e:
        if os.path.exists(file_path): os.remove(file_path)
        return {"error": str(e)}

@app.post("/chat")
async def chat_with_pdf(
    question: str = Form(...), 
    username: str = Form(...), 
    filename: str = Form("None")
):
    try:
        # 1. Call AI logic
        answer = ask_question(question, username, filename)
        
        # 2. Safety: Force answer to be a string
        safe_answer = str(answer) if answer else "I encountered a minor issue processing that. Please try again."

        # 3. Save to History only if file exists
        if filename != "None":
            save_chat_message(username, filename, "user", question)
            save_chat_message(username, filename, "bot", safe_answer)
            
        return {"answer": safe_answer}
    except Exception as e:
        # If the whole process fails, send the error to the chat bubble
        return {"answer": f"⚠️ Connection Issue: The server is busy. Please wait a moment and try again."}

@app.get("/history/{username}/{filename}")
async def fetch_history(username: str, filename: str):
    return {"history": get_chat_history(username, filename)}

@app.get("/sessions/{username}")
async def fetch_sessions(username: str):
    return {"sessions": get_user_files(username)}

if __name__ == "__main__":
    import uvicorn
    # Important: Bind to 0.0.0.0 for cloud deployment
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)