# 🤖 TalkToPDF AI - Full-Stack RAG Platform

TalkToPDF is a professional-grade AI application that allows users to have high-context conversations with any PDF document. Using **Retrieval-Augmented Generation (RAG)**, the system analyzes document content to provide accurate, factual, and formatted responses.

## 🚀 Key Features
- **Multi-Tenant Security:** Metadata filtering ensures users only access their own uploaded documents.
- **Universal Analysis:** Optimized for everything from 1-page resumes to 100-page reports.
- **Hybrid Retrieval:** Uses **MMR (Maximum Marginal Relevance)** and **Head-Tail fetching** to solve the "Lost in the Middle" context problem.
- **Persistent Memory:** MongoDB-backed chat history allows users to resume past conversations.
- **Advanced UI:** Modern React interface with Tailwind CSS v4 and Markdown rendering for professional AI responses.

## 🛠️ Tech Stack
- **Frontend:** React.js, Tailwind CSS v4, Axios, Lucide-Icons.
- **Backend:** Python, FastAPI, LangChain.
- **AI Brain:** Google Gemini 1.5 Flash (LLM), Google Embedding-001.
- **Database:** MongoDB Atlas (Vector Search).

## ⚙️ Setup Instructions

### 1. Backend Setup
1. Navigate to `/backend`.
2. Create a Virtual Environment: `python -m venv venv`.
3. Activate: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux).
4. Install dependencies: `pip install -r requirements.txt`.
5. Setup `.env` file with `MONGO_URI` and `GOOGLE_API_KEY`.
6. Run: `python main.py`.

### 2. Frontend Setup
1. Navigate to `/frontend`.
2. Install dependencies: `npm install`.
3. Run: `npm run dev`.

---
**Developed by Suryanarayan Panda**