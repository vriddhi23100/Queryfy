# Queryfy: An AI-Powered Question Paper Generator

Queryfy is a minimal, fast, and intentionally simple web application that transforms study material into professional assessments.  
Upload a document, choose question type and output format, click Generate - Queryfy handles the rest.

Built for teachers, students, trainers, coaching institutes, and anyone tired of manually crafting question papers or quizzing.

---

## Features

-> Upload PDFs, PPTs, DOCX, or TXT files  
-> Generate MCQs, True/False, Fill-Ups, Short/Long Answer, Numerical questions  
-> Export as: Printable PDF / Editable Word Document / Auto-built Google Form
-> Optional answer key generation  
-> Clean, single-page interface  
-> Temporary file handling — nothing stored after generation  
-> Multi-model ready

---

## Tech Stack

### Frontend
- Vanilla HTML
- CSS
- JavaScript (Fetch API)

### Backend
- Python
- Flask
- Gunicorn (production server)

### AI & Integrations
- Gemini API(primary LLM), Groq API
- Google Forms & Drive API (optional export)

### Processing & Export
- PyPDF2
- python-docx
- python-pptx
- FPDF

---

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/your-username/queryfy.git
cd queryfy
```
### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set environment variables
```bash
GEMINI_API_KEY=your_key_here
SERVICE_ACCOUNT_JSON='{"auth": "..."}'   # optional, enables Google Forms
```

### 5. Run locally
```bash
python app.py
```

## Future Scope
1. OCR support (Tesseract/Cloud Vision)
2. User accounts + document history
3. Redis-based caching + scalable rate limiting
4. Multi-model failover (Gemini → Groq → Claude)
5. Difficulty level & Bloom taxonomy classification
6. Better Google Form quiz automation
