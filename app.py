from flask import Flask, render_template, request, flash, redirect, url_for
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_APP_SECRET_KEY')
UPLOAD_FOLDER = 'uploaded_files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf'}

# MySQL configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://root:''@localhost/plagcheck'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<UploadedFile {self.filename}>'

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
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        uploaded_file = UploadedFile(filename=filename)
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