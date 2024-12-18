from dotenv import load_dotenv
load_dotenv()  # Load environment variables from the .env file

from flask import Flask, request, render_template, send_file
from io import BytesIO
from PyPDF2 import PdfReader
from fpdf import FPDF
import google.generativeai as genai
import unicodedata
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import webbrowser

app = Flask(__name__)

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Google Form and Drive API scopes
SCOPES_FORMS = ['https://www.googleapis.com/auth/forms.body']
SCOPES_DRIVE = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = r'your-jsonfilehere-437108-u7-9873e3487aaf.json'

# Authenticate Google services
creds_forms = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES_FORMS)
creds_drive = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES_DRIVE)
form_service = build('forms', 'v1', credentials=creds_forms)
drive_service = build('drive', 'v3', credentials=creds_drive)

# Function to extract text from a PDF
def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Function to generate questions
def generate_questions(prompt, question_type, num_questions):
    query = ""
    if question_type.lower() == "mcq":
        query = (
            f"Generate {num_questions} HUMAN MADE multiple-choice questions based on the following text: {prompt} "
            "Each question should have 4 options labeled a, b, c, d, with only one correct answer. "
            "Don't use too many 'your thoughts/your opinion' questions. "
            "Include some factual-based and some conceptual mix."
            "DON'T begin question like : based on the text,.. "
            "STRICTLY Output only the questions in the following format:\n\n"
            "1. [Question text]\n   a) [Option 1]\n   b) [Option 2]\n   c) [Option 3]\n   d) [Option 4]\n"
        )
    
    elif question_type.lower() == "true/false":
        query = (
            f"Generate {num_questions} HUMAN MADE true/false questions based on the following text: {prompt} "
            "Don't use too many 'your thoughts/your opinion' questions. "
            "Include some factual-based and some conceptual mix."
            "DON'T begin question like : based on the text,.. "
            "STRICTLY Output only the questions in the following format:\n\n"
            "1. [Question text] (True/False)\n"
        )
    elif question_type.lower() == "fill-ups":
        query = (
            f"Generate {num_questions} HUMAN MADE fill-in-the-blank questions based on the following text: {prompt} "
            "Each question should contain a blank indicated by '_____' where the answer goes. "
            "Don't use too many 'your thoughts/your opinion' questions. "
            "Include some factual-based and some conceptual mix."
            "DON'T begin question like : based on the text,.. "
            "STRICTLY Output only the questions in the following format:\n\n"
            "1. [Sentence with blank]\n"
        )
    else:  # Default to subjective questions
        query = (
            f"Generate {num_questions} HUMAN MADE easy to moderate {question_type} questions based on the following text: {prompt} "
            "Don't use too many 'your thoughts/your opinion' questions. "
            "Include some factual-based and some conceptual mix. "
            "DON'T begin question like : based on the text,.. "
            "STRICTLY Output only the questions in a clean and numbered question paper format.\n\n"
            "1. [Question text]\n"
        )

    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content(query)
    return response.text

# Function to save questions to PDF
def save_questions_to_pdf(raw_questions, subject, marks):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Generated Question Paper", ln=True, align="C")
    pdf.ln(10)
    pdf.cell(0, 10, f"Subject: {subject}", ln=True)
    pdf.cell(0, 10, f"Maximum Marks: {marks}", ln=True)
    pdf.ln(10)
    pdf.multi_cell(0, 10, remove_special_characters(raw_questions))
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output

# Function to remove special characters
def remove_special_characters(text):
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')

# Function to create a Google Form and add questions
def create_google_form(questions, user_email):
    try:
        # Create new form
        new_form = {"info": {"title": "Generated Google Form"}}
        form = form_service.forms().create(body=new_form).execute()
        form_id = form['formId']
        form_url = form["responderUri"]

        print(f"Form created successfully: {form_url}")

        # Share form with provided email if exists
        if user_email:
            share_google_form(form_id, user_email)

        # Split questions by newline and add them to the form
        questions_list = questions.strip().split('\n')
        for question in questions_list:
            if question.strip():  # Skip empty questions
                add_question_to_form(form_service, form_id, question, question_type="text")

        return form_url
    except Exception as e:
        print(f"An error occurred while creating the form: {e}")
        return None

# Function to share Google Form with the provided email
def share_google_form(form_id, user_email):
    permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': user_email
    }
    try:
        drive_service.permissions().create(fileId=form_id, body=permission).execute()
        print(f"Form shared successfully with {user_email}")
    except Exception as e:
        print(f"An error occurred while sharing the form: {e}")

def add_question_to_form(service, form_id, question_text, question_type="text", choices=None):
    # Skip empty questions if any (this is mostly for defense)
    if not question_text.strip():
        print("Skipping empty question.")
        return
    
    # Get the existing questions in the form
    form = service.forms().get(formId=form_id).execute()
    existing_questions = form.get('items', [])
    question_count = len(existing_questions)  # Get current question count

    if question_type == "mcq" and choices:
        # Use the provided question_text as the question and `choices` as the options
        question = {
            "requests": [
                {
                    "createItem": {
                        "item": {
                            "title": question_text,  # Question text
                            "questionItem": {
                                "question": {
                                    "required": True,
                                    "choiceQuestion": {
                                        "type": "RADIO",  # Can also be "CHECKBOX" for multi-select
                                        "options": [{"value": choice} for choice in choices]  # Map choices correctly
                                    }
                                }
                            }
                        },
                        "location": {"index": question_count}  # Add question at the end of the form
                    }
                }
            ]
        }
    else:
        question = {
            "requests": [
                {
                    "createItem": {
                        "item": {
                            "title": question_text,  # Text question
                            "questionItem": {
                                "question": {
                                    "required": True,
                                    "textQuestion": {}  # No choices for text questions
                                }
                            }
                        },
                        "location": {"index": question_count} 
                    }
                }
            ]
        }
    
    try:
        service.forms().batchUpdate(formId=form_id, body=question).execute()
        print(f"Question added: {question_text}")
    except Exception as e:
        print(f"An error occurred while adding the question: {e}")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Extract uploaded file and form data
        uploaded_file = request.files['pdf_file']
        question_type = request.form['question_type']
        num_questions = int(request.form['num_questions'])
        output_format = request.form['output_format']
        subject = request.form.get('subject', 'General')
        marks = request.form.get('marks', '100')
        user_email = request.form.get('email', '').strip()  # Get user email

        if uploaded_file.filename == '':
            return "No file uploaded", 400

        pdf_text = extract_text_from_pdf(uploaded_file)
        questions = generate_questions(pdf_text, question_type, num_questions)

        if output_format == 'pdf':
            pdf_output = save_questions_to_pdf(questions, subject, marks)
            return send_file(
                pdf_output,
                download_name='Generated_Questions.pdf',
                as_attachment=True
            )
        elif output_format == 'form':
            if not user_email:
                return "Email address is required for Google Form sharing.", 400
            form_url = create_google_form(questions, user_email)
            return f"Google Form created: <a href='{form_url}' target='_blank'>Open Form</a>"
        else:
            return "Invalid output format", 400
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@app.route('/create_form', methods=['POST'])
def create_form():
    data = request.json
    questions = data.get('questions', [])
    email_to_share = data.get('email', '')
    
if __name__ == '__main__':
    app.run(debug=True)