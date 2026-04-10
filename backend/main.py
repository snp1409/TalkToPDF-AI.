from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import shutil, os
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
async def chat_with_pdf(question: str = Form(...), username: str = Form(...), filename: str = Form("None")):
    try:
        # Get the cleaned, long response from chat.py
        answer = ask_question(question, username, filename)
        
        # Final safety check
        if not answer:
            answer = "I searched the document but could not generate a clear response. Please rephrase."

        if filename != "None":
            save_chat_message(username, filename, "user", question)
            save_chat_message(username, filename, "bot", str(answer))
            
        return {"answer": str(answer)}
    except Exception as e:
        return {"answer": f"⚠️ Connection error: {str(e)}"}

@app.delete("/delete/{username}/{filename}")
async def delete_file(username: str, filename: str):
    try:
        delete_document_vectors(username, filename)
        delete_file_history(username, filename)
        return {"message": "Deleted"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/history/{username}/{filename}")
async def fetch_history(username: str, filename: str):
    return {"history": get_chat_history(username, filename)}

@app.get("/sessions/{username}")
async def fetch_sessions(username: str):
    return {"sessions": get_user_files(username)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)