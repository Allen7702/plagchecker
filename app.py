from flask import Flask, render_template, request, flash, redirect, url_for
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from io import BytesIO
from PyPDF2 import PdfReader
import docx
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

nltk.download('punkt')
nltk.download('stopwords')

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_APP_SECRET_KEY')
UPLOAD_FOLDER = 'uploaded_files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# MySQL configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://allen:Fantastic3#@localhost/plag_check'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#checks the extension of the filename
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text, nullable=False)  # This is the line you asked about
    upload_date = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<UploadedFile {self.filename}>'
    
#extracts text from pdf file
def extract_text_from_pdf(pdf_file_path):
    with open(pdf_file_path, 'rb') as pdf_file:
        pdf_reader = PdfReader(pdf_file)
        text = ''
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_docx(docx_file_path):
    doc = docx.Document(docx_file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

#preprocesses text
def preprocess_text(text):
    # Convert text to lowercase
    text = text.lower()

    # Remove punctuation
    text = ''.join(c for c in text if c not in string.punctuation)

    # Tokenize words
    words = word_tokenize(text)

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    words = [w for w in words if w not in stop_words]

    # Stem words
    stemmer = PorterStemmer()
    words = [stemmer.stem(w) for w in words]

    return ' '.join(words)

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_file():
    if 'pdfFile' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['pdfFile']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        #  # Reset file pointer to the beginning
        # file.seek(0)

        # # Extract text from PDF file
        # with BytesIO(file.read()) as pdf_file:
        #     pdf_reader = PyPDF2.PdfReader(pdf_file)
        #     text = ''
        #     for page_num in range(len(pdf_reader.pages)):
        #         text += pdf_reader.pages[page_num].extract_text()

        # Extract text from PDF file
        if filename.lower().endswith('.pdf'):
            extracted_text = extract_text_from_pdf(file_path)
        elif filename.lower().endswith('.docx'):
            extracted_text = extract_text_from_docx(file_path)
        else:
            flash('Invalid file type. Please upload PDF or DOCX files.')
            return redirect(request.url)
        
        # Preprocess the text
        preprocessed_text = preprocess_text(extracted_text)

        # Save the filename and extracted text to the database
        uploaded_file = UploadedFile(filename=filename, text=preprocessed_text)
        db.session.add(uploaded_file)
        db.session.commit()

        flash('File successfully uploaded')
        return redirect(url_for('upload_form'))
    else:
        flash('Allowed file types are pdf')
        return redirect(request.url)


@app.route('/uploaded_files')
def uploaded_files():
    files = UploadedFile.query.order_by(UploadedFile.upload_date.desc()).all()
    return render_template('uploaded_files.html', files=files)

if __name__ == '__main__':
    app.run(debug=True)