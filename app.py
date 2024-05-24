from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify
)

import io
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_paginate import Pagination, get_page_args
from database import db, Contact, Document, admin, Category,ContactInfo,PageInformation

app = Flask(__name__, template_folder='template')

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tmproject.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mysecret'

# Initialize database
db.init_app(app)
admin.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def home():
    page_data=PageInformation.query.all()[0]
    contact_info_data = ContactInfo.query.all()
    categories = Category.query.all()
    return render_template('home.html', categories=categories,
                           contact=contact_info_data,
                           page_info=page_data)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        contact = Contact(name=name, email=email, message=message)
        db.session.add(contact)
        db.session.commit()
        return redirect(url_for('contact'))
    return render_template('contact.html')

def get_documents(page, per_page, category_id=None, search_term=None):
    query = Document.query
    if category_id:
        query = query.filter_by(c_id=category_id)
    if search_term:
        query = query.filter(Document.document_filename.ilike(f'%{search_term}%'))
    documents = query.paginate(page=page, per_page=per_page, error_out=False)
    return documents

# Route for download page
@app.route('/download_page')
def download_page():
    # Get category ID from URL
    category_id = request.args.get('category_id', type=int)

    # Get page number from URL, default to 1 if not provided
    page = request.args.get('page', default=1, type=int)

    # Number of documents per page
    per_page = 4

    # Query documents with optional category filtering
    if category_id:
        documents_query = Document.query.filter_by(category_id=category_id)
    else:
        documents_query = Document.query

    # Paginate the documents
    documents = documents_query.paginate(page=page, per_page=per_page, error_out=False)

    # Get all categories
    categories = Category.query.all()

    # Render the download page template
    return render_template('download_page.html', documents=documents.items, pagination=documents, categories=categories, current_category=category_id)





@app.route('/search')
def search_documents():
   
    
    search_term = request.args.get('q')
    category_id = request.args.get('category_id')

    if search_term.strip()=='':
        return render_template('document_list.html', documents=None)
    
    page, per_page, _ = get_page_args(page_parameter='page', per_page_parameter='per_page')
    
    documents = get_documents(page, per_page, search_term=search_term)
    pagination = Pagination(page=page, total=documents.total, per_page=per_page, css_framework='bootstrap4')
    
    return render_template('document_list.html', documents=documents.items, pagination=pagination)





from flask import send_file

@app.route('/get_document', methods=['GET'])
def get_document():
    document_id = request.args.get('document_id')
    if not document_id:
        return jsonify({'error': 'No document ID provided'}), 400
    
    document = Document.query.get(document_id)
    print('document is : ',document)
    if not document:
        return jsonify({'error': 'Document not found'}), 404
        # Serve the document file from binary data stored in the database
    return send_file(
        io.BytesIO(document.document),
        mimetype='application/pdf',
        as_attachment=True,  # Set to True to force download
         download_name=document.document_filename  # Specify filename for the downloaded file
    )



@app.route('/submit_contact_form', methods=['POST'])
def submit_contact_form():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Create a new Contact object
        new_contact = Contact(name=name, email=email, message=message)

        # Add the new contact to the database session
        db.session.add(new_contact)

        # Commit the session to save the contact to the database
        db.session.commit()

        return redirect('/thank_you')

@app.route('/thank_you')
def thank_you():
    return "Thank you for your message! We'll get back to you soon."

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
